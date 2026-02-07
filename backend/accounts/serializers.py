from django.contrib.auth import get_user_model, authenticate
from django.db import transaction

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import StudentProfile, TeacherProfile, OTPToken


UserModel = get_user_model()

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        style={'input_type':'password'}
    )
    def authenticate(self, **kwargs):
        return authenticate(self.context["request"], **kwargs)

    def _validate_username(self, username, password):
        user = None
        if username and password :
            user = self.authenticate(username=username, password=password)
        else:
            msg = "Must include username and password."
            raise ValidationError(msg)
        return user
    
    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        user = self._validate_username(username, password)
        if user:
            if not user.is_active:
                msg = "User account is disabled."
                raise ValidationError(msg)
        else:
            msg = "Unable to log in with provided credentials."
            raise ValidationError(msg)
        
        attrs['user'] = user
        return attrs
    

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        style={'input_type':'password'},
        write_only=True
    )
    confirm_password = serializers.CharField(
        style={'input_type':'password'},
        write_only=True
    )
    is_student = serializers.BooleanField()
    class Meta:
        model = UserModel
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
            'confirm_password',
            'is_student',
        ]
    def validate(self, attrs):
        attrs = super().validate(attrs)
        password = attrs.get('password')
        confirm_password = attrs.get("confirm_password")
        if password != confirm_password:
            raise ValidationError("Two passwords must match.")
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop("confirm_password")
        with transaction.atomic():
            user = UserModel.objects.create_user(**validated_data)
            if user.is_student:
                StudentProfile.objects.create(user=user)
            else:
                TeacherProfile.objects.create(user=user)
        return user
    

class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = (
            'id',
            'roll_no',
            'department',
            'current_semester',
            'batch_year',
            'section'
        )

class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = (
            'department',
            'phone_number',
            'designation',
            'is_full_time',
        )

class UserDetailsSerializer(serializers.ModelSerializer):
    """
    User model w/o password
    """
    profile = serializers.SerializerMethodField()
    class Meta:
        model = UserModel
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')
    
    def get_profile(self, obj):
        if hasattr(obj, 'student_profile'):
            return StudentProfileSerializer(obj.student_profile).data
        
        if hasattr(obj, "teacher_profile"):
            return TeacherProfileSerializer(obj.teacher_profile).data
        
        return None
    
class OTPTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTPToken
        fields = (
            'id',
            'user',
            'token',
            'created_at'
        )
        read_only_fields = ("id", "user", "created_at")



class EnterEmailForPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class EnterOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True)

class CreatePasswordFromResetOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    reset_token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    

        
