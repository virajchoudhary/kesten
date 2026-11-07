from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db.models import CharField, Q, Value
from django.db.models.functions import Cast, Replace
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from workspace.serializers import ErrorSerializer
from workspace.views import PrivateAPIView, api_error

from .comparison import compare_run_compatibility
from .models import ResearchDataset, ResearchRun
from .replay import replay_run, result_hash
from .serializers import (
    DatasetListSerializer,
    DatasetSerializer,
    ResearchCompareSerializer,
    ResearchExportSerializer,
    ResearchHistoryQuerySerializer,
    ResearchHistorySerializer,
    ResearchInputSerializer,
    ResearchReplayRequestSerializer,
    ResearchReplaySerializer,
    ResearchRunListSerializer,
    ResearchRunSerializer,
    ResearchRunSummarySerializer,
)
from .services import (
    DatasetUnavailable,
    ResearchConflict,
    dataset_info,
    run_evaluation,
    run_info,
    validate_synthetic_export,
)


class ResearchAPIView(PrivateAPIView):
    def initial(self, request, *args, **kwargs):
        if getattr(settings, "CADRISYN_RELEASE_PROFILE", "development") == "demo":
            raise NotFound("Private research is unavailable in the demo-only release profile.")
        return super().initial(request, *args, **kwargs)


class DatasetsView(ResearchAPIView):
    @extend_schema(responses={200: DatasetListSerializer, 403: ErrorSerializer}, operation_id="research_datasets")
    def get(self, request):
        datasets = ResearchDataset.objects.filter(owner=request.user)[:100]
        return Response(DatasetListSerializer({"items": [dataset_info(item) for item in datasets]}).data)


class RunsView(ResearchAPIView):
    parser_classes = (JSONParser,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "research"

    def get_throttles(self):
        return super().get_throttles() if self.request.method == "POST" else []

    @extend_schema(responses={200: ResearchRunListSerializer, 403: ErrorSerializer}, operation_id="research_runs")
    def get(self, request):
        runs = ResearchRun.objects.filter(owner=request.user).select_related("dataset")[:20]
        return Response(ResearchRunListSerializer({"items": [run_info(item) for item in runs]}).data)

    @extend_schema(request=ResearchInputSerializer, responses={201: ResearchRunSerializer, 200: ResearchRunSerializer, 400: ErrorSerializer, 403: ErrorSerializer, 404: ErrorSerializer, 409: ErrorSerializer, 415: ErrorSerializer, 429: ErrorSerializer, 503: ErrorSerializer}, operation_id="research_evaluate")
    def post(self, request):
        serializer = ResearchInputSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error("invalid_input", "Choose a private dataset and supported horizon.", 400, serializer.errors)
        values = serializer.validated_data
        dataset = get_object_or_404(ResearchDataset, id=values["dataset_id"], owner=request.user)
        try:
            run, created = run_evaluation(
                owner=request.user, dataset=dataset, horizon=values["horizon_sessions"],
                idempotency_key=values["idempotency_key"],
            )
        except ResearchConflict:
            return api_error("request_key_conflict", "This request key was already used with different inputs.", 409)
        except DatasetUnavailable:
            return api_error("dataset_unavailable", "The dataset cannot be evaluated under this research protocol.", 503)
        return Response(ResearchRunSerializer(run_info(run)).data, status=201 if created else 200)


class RunView(ResearchAPIView):
    @extend_schema(responses={200: ResearchRunSerializer, 403: ErrorSerializer, 404: ErrorSerializer}, operation_id="research_run_read")
    def get(self, request, run_id):
        run = get_object_or_404(ResearchRun.objects.select_related("dataset"), id=run_id, owner=request.user)
        return Response(ResearchRunSerializer(run_info(run)).data)


class ResearchHistoryView(ResearchAPIView):
    @extend_schema(
        parameters=[ResearchHistoryQuerySerializer],
        responses={200: ResearchHistorySerializer, 400: ErrorSerializer, 403: ErrorSerializer, 503: ErrorSerializer},
        operation_id="research_history",
    )
    def get(self, request):
        serializer = ResearchHistoryQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return api_error("invalid_query", "Use the declared research filters and pagination.", 400, serializer.errors)

        filters = serializer.validated_data
        runs = ResearchRun.objects.filter(owner=request.user)
        query = filters.get("q", "")
        if query:
            runs = runs.annotate(
                _run_id_text=Replace(Cast("id", output_field=CharField()), Value("-"), Value("")),
                _dataset_id_text=Replace(Cast("dataset_id", output_field=CharField()), Value("-"), Value("")),
            ).filter(
                Q(dataset__payload__name__icontains=query)
                | Q(dataset__payload__instrument_id__icontains=query)
                | Q(_run_id_text__icontains=query.replace("-", ""))
                | Q(_dataset_id_text__icontains=query.replace("-", ""))
            )
        instrument_id = filters.get("instrument_id")
        if instrument_id:
            runs = runs.filter(dataset__payload__instrument_id=instrument_id)
        horizon_sessions = filters.get("horizon_sessions")
        if horizon_sessions not in (None, ""):
            runs = runs.filter(horizon_sessions=horizon_sessions)
        data_kind = filters.get("data_kind")
        if data_kind:
            runs = runs.filter(dataset__payload__data_kind=data_kind)

        offset = filters["offset"]
        limit = filters["limit"]
        total = runs.count()
        rows = runs.order_by("-created_at", "-id").values(
            "id",
            "dataset_id",
            "dataset__version",
            "result__dataset_version",
            "dataset__payload__name",
            "dataset__payload__data_kind",
            "dataset__payload__instrument_id",
            "horizon_sessions",
            "created_at",
            "completed_at",
        )[offset:offset + limit]
        rows = list(rows)
        if any(row["result__dataset_version"] != row["dataset__version"] for row in rows):
            return api_error(
                "history_integrity_unavailable",
                "A saved evaluation has inconsistent dataset lineage and cannot be listed.",
                503,
            )
        items = [
            {
                "id": row["id"],
                "dataset_id": row["dataset_id"],
                "dataset_version": row["result__dataset_version"],
                "name": row["dataset__payload__name"],
                "data_kind": row["dataset__payload__data_kind"],
                "instrument_id": row["dataset__payload__instrument_id"],
                "horizon_sessions": row["horizon_sessions"],
                "created_at": row["created_at"],
                "completed_at": row["completed_at"],
                "status": "succeeded",
            }
            for row in rows
        ]
        return Response(ResearchHistorySerializer({
            "items": ResearchRunSummarySerializer(items, many=True).data,
            "total": total,
            "offset": offset,
            "limit": limit,
        }).data)


class ResearchReplayView(ResearchAPIView):
    parser_classes = (JSONParser,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "research"

    def get_throttles(self):
        return super().get_throttles() if self.request.method == "POST" else []

    @extend_schema(
        request=ResearchReplayRequestSerializer,
        responses={
            200: ResearchReplaySerializer,
            400: ErrorSerializer,
            403: ErrorSerializer,
            404: ErrorSerializer,
            415: ErrorSerializer,
            429: ErrorSerializer,
            503: ErrorSerializer,
        },
        operation_id="research_run_replay",
    )
    def post(self, request, run_id):
        run = get_object_or_404(ResearchRun.objects.select_related("dataset"), id=run_id, owner=request.user)
        serializer = ResearchReplayRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error("invalid_body", "Replay accepts an empty JSON object.", 400, serializer.errors)
        try:
            receipt = replay_run(run)
        except (KeyError, OverflowError, TypeError, ValueError):
            return api_error("replay_unavailable", "The saved run cannot be replayed under its data and protocol.", 503)
        return Response(ResearchReplaySerializer(receipt).data)


class ResearchExportView(ResearchAPIView):
    @extend_schema(
        responses={
            200: ResearchExportSerializer,
            403: ErrorSerializer,
            404: ErrorSerializer,
        },
        operation_id="research_run_export",
    )
    def get(self, request, run_id):
        run = get_object_or_404(ResearchRun.objects.select_related("dataset"), id=run_id, owner=request.user)
        try:
            validate_synthetic_export(run)
            dataset_serializer = DatasetSerializer(data=dataset_info(run.dataset))
            run_serializer = ResearchRunSerializer(data=run_info(run))
            if not dataset_serializer.is_valid() or not run_serializer.is_valid():
                return api_error(
                    "export_unavailable",
                    "Only a consistent synthetic pipeline check can be exported.",
                    403,
                )
            digest = result_hash(run.result)
        except (KeyError, OverflowError, TypeError, ValueError):
            return api_error(
                "export_unavailable",
                "Only a consistent synthetic pipeline check can be exported.",
                403,
            )

        body = {
            "format": "cadrisyn-research-v1",
            "disclosure": "Synthetic pipeline check. Not empirical market evidence.",
            "dataset": dataset_serializer.data,
            "run": {**run_serializer.data, "result": run.result},
            "result_sha256": digest,
        }
        response = Response(body, content_type="application/json")
        response["Content-Disposition"] = f'attachment; filename="cadrisyn-run-{run.id}.json"'
        response["X-Content-Type-Options"] = "nosniff"
        return response


class ResearchCompareView(ResearchAPIView):
    @extend_schema(
        responses={
            200: ResearchCompareSerializer,
            403: ErrorSerializer,
            404: ErrorSerializer,
        },
        operation_id="research_runs_compare",
    )
    def get(self, request, run_id, other_id):
        left = get_object_or_404(ResearchRun.objects.select_related("dataset"), id=run_id, owner=request.user)
        right = get_object_or_404(ResearchRun.objects.select_related("dataset"), id=other_id, owner=request.user)
        comparison = compare_run_compatibility(left, right)
        return Response(ResearchCompareSerializer(comparison).data)
