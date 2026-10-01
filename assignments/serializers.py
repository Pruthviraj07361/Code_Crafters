from rest_framework import serializers

from .models import Meeting, ProblemStatement


# --- Input serializers (plain, used by supervisor POST endpoints) ---

class ProblemStatementCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    # Kept as-is (no whitespace trimming): a trailing newline can matter
    # when the text is later fed to a program as stdin.
    sample_input = serializers.CharField(
        required=False, allow_blank=True, trim_whitespace=False
    )
    test_cases = serializers.JSONField()
    week_number = serializers.IntegerField(
        required=False, allow_null=True, min_value=1
    )

    def validate_test_cases(self, value):
        if not isinstance(value, list) or not value:
            raise serializers.ValidationError('Provide at least one grading test case.')

        for index, test_case in enumerate(value, start=1):
            if not isinstance(test_case, dict):
                raise serializers.ValidationError(f'Test case {index} must be an object.')
            if not isinstance(test_case.get('input'), str):
                raise serializers.ValidationError(f'Test case {index} needs string input.')
            if not isinstance(test_case.get('expected_output'), str):
                raise serializers.ValidationError(
                    f'Test case {index} needs string expected_output.'
                )
        return value


class MeetingUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    notes = serializers.CharField(required=False, allow_blank=True)
    scheduled_for = serializers.DateTimeField()


# --- Read-only serializers ---

class SupervisorProblemStatementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ProblemStatement
        fields = [
            'id', 'title', 'description', 'sample_input', 'test_cases', 'week_number',
            'created_at', 'created_by_name',
        ]

    def get_created_by_name(self, obj):
        return obj.created_by.name if obj.created_by else None


class StudentProblemStatementListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProblemStatement
        fields = ['id', 'title', 'week_number', 'created_at']


class StudentProblemStatementDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProblemStatement
        fields = [
            'id', 'title', 'description', 'sample_input', 'week_number',
            'created_at',
        ]


class SupervisorMeetingSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Meeting
        fields = ['id', 'title', 'notes', 'scheduled_for', 'updated_at', 'updated_by_name']

    def get_updated_by_name(self, obj):
        return obj.updated_by.name if obj.updated_by else None


class StudentMeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = ['title', 'notes', 'scheduled_for', 'updated_at']
