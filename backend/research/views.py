from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from workspace.serializers import ErrorSerializer
from workspace.views import PrivateAPIView, api_error

from .models import ResearchDataset, ResearchRun
from .serializers import (
    DatasetListSerializer,
    ResearchInputSerializer,
    ResearchRunListSerializer,
    ResearchRunSerializer,
)
from .services import (
    DatasetUnavailable,
    ResearchConflict,
    dataset_info,
    run_evaluation,
    run_info,
)


class DatasetsView(PrivateAPIView):
    @extend_schema(responses={200: DatasetListSerializer, 403: ErrorSerializer}, operation_id="research_datasets")
    def get(self, request):
        datasets = ResearchDataset.objects.filter(owner=request.user)[:100]
        return Response(DatasetListSerializer({"items": [dataset_info(item) for item in datasets]}).data)


class RunsView(PrivateAPIView):
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


class RunView(PrivateAPIView):
    @extend_schema(responses={200: ResearchRunSerializer, 403: ErrorSerializer, 404: ErrorSerializer}, operation_id="research_run_read")
    def get(self, request, run_id):
        run = get_object_or_404(ResearchRun.objects.select_related("dataset"), id=run_id, owner=request.user)
        return Response(ResearchRunSerializer(run_info(run)).data)
