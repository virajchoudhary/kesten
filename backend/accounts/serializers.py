from rest_framework import serializers


class PasswordPairSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        max_length=256,
        trim_whitespace=False,
        write_only=True,
    )
    confirm_password = serializers.CharField(
        max_length=256,
        trim_whitespace=False,
        write_only=True,
    )

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": ["The passwords do not match."]}
            )
        return attrs


class InvitationAcceptSerializer(PasswordPairSerializer):
    token = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)


class PasswordResetConfirmSerializer(PasswordPairSerializer):
    token = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)


class ChangePasswordSerializer(PasswordPairSerializer):
    current_password = serializers.CharField(
        max_length=256,
        trim_whitespace=False,
        write_only=True,
    )


class RevokeSessionsSerializer(serializers.Serializer):
    scope = serializers.ChoiceField(choices=["others", "all"])


class InvitationAcceptedSerializer(serializers.Serializer):
    created = serializers.BooleanField()


class PasswordChangedSerializer(serializers.Serializer):
    password_changed = serializers.BooleanField()


class SessionRevocationSerializer(serializers.Serializer):
    revoked = serializers.CharField()
    authenticated = serializers.BooleanField()
    csrf_token = serializers.CharField(allow_null=True)


class AccountErrorSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    field_errors = serializers.JSONField()
    request_id = serializers.CharField()
