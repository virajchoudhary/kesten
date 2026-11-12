from rest_framework import serializers

from .instruments import BY_ID


class InstrumentSerializer(serializers.Serializer):
    id = serializers.CharField()
    symbol = serializers.CharField()
    name = serializers.CharField()
    exchange = serializers.CharField()
    currency = serializers.CharField()
    timezone = serializers.CharField()


class InstrumentListSerializer(serializers.Serializer):
    items = InstrumentSerializer(many=True)


class SearchSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=80, allow_blank=True, default="")


class WatchlistInputSerializer(serializers.Serializer):
    instrument_id = serializers.ChoiceField(choices=list(BY_ID))


class BarQuerySerializer(serializers.Serializer):
    range = serializers.ChoiceField(choices=["1m", "3m", "6m", "1y", "2y"], default="1y")
    mode = serializers.ChoiceField(choices=["demo", "market"], default="demo")


class BarSerializer(serializers.Serializer):
    time = serializers.DateField()
    open = serializers.FloatField()
    high = serializers.FloatField()
    low = serializers.FloatField()
    close = serializers.FloatField()
    volume = serializers.FloatField()


class IndicatorPointSerializer(serializers.Serializer):
    time = serializers.DateField()
    value = serializers.FloatField()


class IndicatorsSerializer(serializers.Serializer):
    sma20 = IndicatorPointSerializer(many=True)
    sma50 = IndicatorPointSerializer(many=True)
    rsi14 = IndicatorPointSerializer(many=True)


class ProvenanceSerializer(serializers.Serializer):
    data_mode = serializers.ChoiceField(choices=["demo", "delayed"])
    source_id = serializers.CharField()
    source_label = serializers.CharField()
    as_of = serializers.DateField()
    fetched_at = serializers.DateTimeField()
    price_basis = serializers.CharField()
    freshness_state = serializers.ChoiceField(choices=["current", "stale", "partial", "unavailable"])
    market_state = serializers.ChoiceField(choices=["open", "closed", "unknown"])
    delay_seconds = serializers.IntegerField(allow_null=True)
    snapshot_id = serializers.CharField()
    disclaimer = serializers.CharField()


class MarketResponseSerializer(serializers.Serializer):
    instrument = InstrumentSerializer()
    bars = BarSerializer(many=True)
    indicators = IndicatorsSerializer()
    provenance = ProvenanceSerializer()


class UserSerializer(serializers.Serializer):
    username = serializers.CharField()
    is_staff = serializers.BooleanField()


class SessionSerializer(serializers.Serializer):
    authenticated = serializers.BooleanField()
    user = UserSerializer(allow_null=True)
    csrf_token = serializers.CharField()
    market_data_enabled = serializers.BooleanField()
    legacy_enabled = serializers.BooleanField()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=256, trim_whitespace=False, write_only=True)


class ErrorSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    field_errors = serializers.JSONField()
    request_id = serializers.CharField()
