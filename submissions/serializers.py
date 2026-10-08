from rest_framework import serializers

from .models import Submission


class SubmissionCreateSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=Submission.LANGUAGE_CHOICES)
    code = serializers.CharField(trim_whitespace=False)


class SubmissionListSerializer(serializers.ModelSerializer):
    problem_title = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = ['id', 'problem_statement', 'problem_title', 'language', 'status', 'submitted_at']

    def get_problem_title(self, obj):
        return obj.problem_statement.title


class SubmissionDetailSerializer(serializers.ModelSerializer):
    problem_title = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            'id',
            'problem_statement',
            'problem_title',
            'language',
            'code',
            'status',
            'judge0_output',
            'attempt_count',
            'submitted_at',
            'checked_at',
        ]

    def get_problem_title(self, obj):
        return obj.problem_statement.title
