from rest_framework import serializers


class DatasetSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    instrument_id = serializers.CharField()
    data_kind = serializers.ChoiceField(choices=["synthetic_fixture", "historical"])
    version = serializers.CharField()
    source_id = serializers.CharField()
    license_reference = serializers.CharField()
    availability_evidence = serializers.CharField()
    adjustment_basis = serializers.CharField()
    calendar = serializers.CharField()
    observation_count = serializers.IntegerField()
    first_session = serializers.DateField()
    last_session = serializers.DateField()
    created_at = serializers.DateTimeField()


class DatasetListSerializer(serializers.Serializer):
    items = DatasetSerializer(many=True)


class ResearchInputSerializer(serializers.Serializer):
    dataset_id = serializers.UUIDField()
    horizon_sessions = serializers.ChoiceField(choices=[1, 5])
    idempotency_key = serializers.UUIDField()

    def to_internal_value(self, data):
        if isinstance(data, dict) and (
            set(data) - set(self.fields) or type(data.get("horizon_sessions")) is not int
        ):
            raise serializers.ValidationError({"non_field_errors": ["Use only the declared dataset, integer horizon and request key."]})
        return super().to_internal_value(data)


class RuntimeSerializer(serializers.Serializer):
    python = serializers.CharField()
    engine_source_sha256 = serializers.CharField()
    dependency_lock_sha256 = serializers.CharField()
    dependencies = serializers.DictField(child=serializers.CharField())
    random_seed = serializers.IntegerField(allow_null=True)
    deterministic = serializers.BooleanField()


class TargetSerializer(serializers.Serializer):
    name = serializers.ChoiceField(choices=["split_neutral_close"])
    horizon_sessions = serializers.ChoiceField(choices=[1, 5])
    units = serializers.CharField()
    return_convention = serializers.ChoiceField(choices=["simple price return"])


class ProtocolSerializer(serializers.Serializer):
    id = serializers.CharField()
    train_start = serializers.DateField()
    train_end = serializers.DateField()
    validation_start = serializers.DateField()
    validation_end = serializers.DateField()
    test_start = serializers.DateField()
    test_end = serializers.DateField()
    training_policy = serializers.CharField()
    configuration_trials = serializers.IntegerField()
    directional_policy = serializers.CharField()
    issue_lag_minutes = serializers.IntegerField()
    protocol_sha256 = serializers.CharField()


class MethodSerializer(serializers.Serializer):
    id = serializers.ChoiceField(choices=["last_close", "historical_log_mean"])
    label = serializers.CharField()
    version = serializers.CharField()


class EvaluationSerializer(serializers.Serializer):
    model_id = serializers.ChoiceField(choices=["last_close", "historical_log_mean"])
    partition = serializers.ChoiceField(choices=["validation", "test"])
    n = serializers.IntegerField(min_value=1)
    mae = serializers.FloatField(min_value=0)
    rmse = serializers.FloatField(min_value=0)
    return_mae = serializers.FloatField(min_value=0)
    return_rmse = serializers.FloatField(min_value=0)
    directional_accuracy = serializers.FloatField(min_value=0, max_value=1)
    direction_confusion = serializers.ListField(
        child=serializers.ListField(child=serializers.IntegerField(min_value=0), min_length=3, max_length=3),
        min_length=3, max_length=3,
    )
    mae_difference_vs_last_close = serializers.FloatField()


class EvaluationRowSerializer(serializers.Serializer):
    model_id = serializers.ChoiceField(choices=["last_close", "historical_log_mean"])
    partition = serializers.ChoiceField(choices=["validation", "test"])
    origin = serializers.DateField()
    target = serializers.DateField()
    information_cutoff = serializers.DateTimeField()
    origin_value = serializers.FloatField()
    predicted = serializers.FloatField()
    actual = serializers.FloatField()
    input_sha256 = serializers.CharField()


class ForecastPointSerializer(serializers.Serializer):
    time = serializers.DateField()
    value = serializers.FloatField()


class MethodForecastSerializer(serializers.Serializer):
    model_id = serializers.ChoiceField(choices=["last_close", "historical_log_mean"])
    points = ForecastPointSerializer(many=True)


class ForecastSerializer(serializers.Serializer):
    origin = serializers.DateField()
    information_cutoff = serializers.DateTimeField()
    history = ForecastPointSerializer(many=True)
    models = MethodForecastSerializer(many=True)


class ResearchResultSerializer(serializers.Serializer):
    schema_version = serializers.IntegerField()
    engine_version = serializers.CharField()
    dataset_version = serializers.CharField()
    data_kind = serializers.ChoiceField(choices=["synthetic_fixture", "historical"])
    empirical_performance_established = serializers.BooleanField()
    evidence_kind = serializers.ChoiceField(choices=["synthetic_pipeline_check", "historical_walk_forward"])
    target = TargetSerializer()
    protocol = ProtocolSerializer()
    models = MethodSerializer(many=True)
    evaluation = EvaluationSerializer(many=True)
    evaluation_rows = EvaluationRowSerializer(many=True)
    forecast = ForecastSerializer()
    limitations = serializers.ListField(child=serializers.CharField())


class ResearchRunSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    dataset_id = serializers.UUIDField()
    dataset_version = serializers.CharField()
    name = serializers.CharField()
    data_kind = serializers.ChoiceField(choices=["synthetic_fixture", "historical"])
    instrument_id = serializers.CharField()
    horizon_sessions = serializers.ChoiceField(choices=[1, 5])
    created_at = serializers.DateTimeField()
    started_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField()
    attempts = serializers.IntegerField()
    status = serializers.ChoiceField(choices=["succeeded"])
    result = ResearchResultSerializer()
    runtime = RuntimeSerializer()
    error_code = serializers.CharField(allow_null=True)


class ResearchRunListSerializer(serializers.Serializer):
    items = ResearchRunSerializer(many=True)


class ResearchHistoryQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, max_length=128, trim_whitespace=True)
    instrument_id = serializers.CharField(required=False, allow_blank=True, max_length=32, trim_whitespace=True)
    horizon_sessions = serializers.ChoiceField(choices=[1, 5], required=False, allow_blank=True)
    data_kind = serializers.ChoiceField(
        choices=["synthetic_fixture", "historical"], required=False, allow_blank=True
    )
    offset = serializers.IntegerField(required=False, default=0, min_value=0, max_value=2147483647)
    limit = serializers.IntegerField(required=False, default=20, min_value=1, max_value=50)

    def to_internal_value(self, data):
        if hasattr(data, "keys") and set(data.keys()) - set(self.fields):
            raise serializers.ValidationError(
                {"non_field_errors": ["Use only the declared filters and pagination fields."]}
            )
        return super().to_internal_value(data)


class ResearchRunSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    dataset_id = serializers.UUIDField()
    dataset_version = serializers.CharField()
    name = serializers.CharField()
    data_kind = serializers.ChoiceField(choices=["synthetic_fixture", "historical"])
    instrument_id = serializers.CharField()
    horizon_sessions = serializers.ChoiceField(choices=[1, 5])
    created_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField()
    status = serializers.ChoiceField(choices=["succeeded"])


class ResearchHistorySerializer(serializers.Serializer):
    items = ResearchRunSummarySerializer(many=True)
    total = serializers.IntegerField(min_value=0)
    offset = serializers.IntegerField(min_value=0)
    limit = serializers.IntegerField(min_value=1, max_value=50)


class ResearchReplayRequestSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if type(data) is not dict or data:
            raise serializers.ValidationError(
                {"non_field_errors": ["Replay accepts an empty JSON object."]}
            )
        return {}


class ResearchReplaySerializer(serializers.Serializer):
    run_id = serializers.UUIDField()
    result = serializers.ChoiceField(choices=["PASS", "FAIL"])
    dataset_matches = serializers.BooleanField()
    engine_matches = serializers.BooleanField()
    dependency_lock_matches = serializers.BooleanField()
    runtime_versions_match = serializers.BooleanField()
    result_matches = serializers.BooleanField()
    result_sha256 = serializers.CharField()


class ResearchExportSerializer(serializers.Serializer):
    format = serializers.ChoiceField(choices=["cadrisyn-research-v1"])
    disclosure = serializers.ChoiceField(
        choices=["Synthetic pipeline check. Not empirical market evidence."]
    )
    dataset = DatasetSerializer()
    run = ResearchRunSerializer()
    result_sha256 = serializers.CharField()


class ResearchCompareSerializer(serializers.Serializer):
    left_id = serializers.UUIDField()
    right_id = serializers.UUIDField()
    compatible = serializers.BooleanField()
    reasons = serializers.ListField(child=serializers.CharField())
