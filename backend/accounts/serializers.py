from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import StudentProfile
from django.contrib.auth import get_user_model, authenticate

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
    class Meta:
        model = UserModel
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
            'confirm_password'
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
        return super().create(validated_data)
    

class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = [
            'id',
            'roll_no',
            'department',
            'current_semester',
            'batch_year',
            'section'
        ]
