from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ActivityLog, AdminProfile, StudentProfile

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class StudentRegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    division = serializers.CharField(max_length=10)
    division_roll_number = serializers.CharField(max_length=20)
    branch = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    enrollment_number = serializers.CharField(max_length=50)
    semester = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def validate_enrollment_number(self, value):
        value = value.strip()
        if StudentProfile.objects.filter(enrollment_number=value).exists():
            raise serializers.ValidationError('This enrollment number is already registered.')
        return value

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        StudentProfile.objects.create(
            user=user,
            name=validated_data['name'],
            division=validated_data['division'],
            division_roll_number=validated_data['division_roll_number'],
            branch=validated_data['branch'],
            phone=validated_data['phone'],
            enrollment_number=validated_data['enrollment_number'],
            semester=validated_data.get('semester'),
        )
        return user


class AdminRegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=8)
    requested_role = serializers.ChoiceField(
        choices=[
            (AdminProfile.STAFF_FACULTY, 'Faculty'),
            (AdminProfile.STAFF_SUPERVISOR, 'Supervisor'),
        ],
        required=False,
        allow_blank=True,
        default='',
    )

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        AdminProfile.objects.create(
            user=user,
            name=validated_data['name'],
            phone=validated_data['phone'],
            staff_type=validated_data['requested_role'],
        )
        return user


class PendingStudentSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'email', 'name', 'division', 'division_roll_number',
            'branch', 'phone', 'enrollment_number', 'semester',
        ]


class StudentApprovalActionSerializer(serializers.Serializer):
    # False rejects the registration instead of approving it.
    approved = serializers.BooleanField(default=True)


class PendingStaffSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = AdminProfile
        fields = ['id', 'email', 'name', 'phone', 'staff_type', 'is_approved']


class StaffRoleAssignSerializer(serializers.Serializer):
    staff_type = serializers.ChoiceField(choices=AdminProfile.STAFF_TYPE_CHOICES)
    # False rejects the registration instead of approving it.
    approved = serializers.BooleanField(default=True)


class StudentProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ['division', 'division_roll_number', 'semester']
        extra_kwargs = {
            'semester': {'required': False, 'allow_null': True},
        }

    def validate_semester(self, value):
        if value is not None and value < 1:
            raise serializers.ValidationError('Semester must be at least 1.')
        return value


class ActivityLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = ['id', 'category', 'action', 'description', 'actor_name', 'created_at']

    def get_actor_name(self, obj):
        if obj.actor is None:
            return 'System'
        profile = getattr(obj.actor, 'admin_profile', None)
        return (profile.name if profile is not None else obj.actor.get_full_name()) or obj.actor.username
