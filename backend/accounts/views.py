import secrets

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from django.contrib.auth import (
    login as django_login,
    logout as django_logout,
)
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication

from django.core.mail import send_mail

from .models import (
    StudentProfile,
    OTPToken
)
from .serializers import (
    UserSerializer, 
    LoginSerializer, 
    UserDetailsSerializer,
    EnterEmailForPasswordResetSerializer,
    OTPTokenSerializer,
    EnterOTPSerializer,
    CreatePasswordFromResetOTPSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer
)


UserModel = get_user_model()

class RegisterUserAPIView(generics.CreateAPIView):
    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny, )


class LoginView(generics.GenericAPIView):
    """
    Calls Django Auth login method to register User ID
    in Django session framework

    Accept the following POST parameters: username, password
    """
    permission_classes = (AllowAny, )
    serializer_class = LoginSerializer

    def process_login(self):
        django_login(self.request, self.user)

    def login(self):
        self.user = self.serializer.validated_data['user']
        self.token = None

        if getattr(settings, 'REST_SESSION_LOGIN', True):
            self.process_login()

    def post(self, request, *args, **kwargs):
        self.request = request
        self.serializer = self.get_serializer(
            data=self.request.data, 
            context={'request':self.request}
            )
        self.serializer.is_valid(raise_exception=True)
        self.login()
        
        data = {
            "detail": "Successfully logged in."
        }

        if self.token:
            data["token"] = self.token.key

        response = Response(data, status=status.HTTP_200_OK)
        
        return response

        
class LogoutView(APIView):
    """
        For session authentication, call django logout.
    """
    permission_classes = (IsAuthenticated, )

        
    def post(self, request, *args, **kwargs):
        return self.logout(request)
    
    def logout(self, request):

        if getattr(settings, 'REST_SESSION_LOGIN', True):
            django_logout(request)

        response = Response({"detail": "Successfully logout."}, status=status.HTTP_200_OK)

        return response
    
 
class UserDetailsView(generics.RetrieveUpdateAPIView):
    """
    Reads and updates UserModel fields
    Accepts GET, PUT, PATCH methods.

    Default accepted fields: username, first_name, last_name
    Default display fields: pk, username, email, first_name, last_name
    Read-only fields: pk

    Returns UserModel fields.
    """
    queryset = UserModel.objects.all()
    serializer_class = UserDetailsSerializer
    permission_classes = (IsAuthenticated, )

    def get_object(self):
        return self.request.user

class UserProfileDetailsView(generics.RetrieveAPIView):
    """
    General class for just viewing the profile of any user[student, teachers]
    """
    queryset = UserModel.objects.all()
    serializer_class = UserDetailsSerializer
    lookup_field = "username"

class ProfileRetrieveUpdateView(generics.CreateAPIView, generics.RetrieveUpdateAPIView):
    queryset = StudentProfile.objects.all()
    permission_classes = (IsAuthenticated, )

    def _is_student(self, user):
        if user.is_student:
            return user.student_profile
        return user.teacher_profile
    
    def get_object(self):
        return self._is_student(self.request.user)
    
    def get_serializer_class(self):
        if self.request.user.is_student:
            return StudentProfileSerializer
        return TeacherProfileSerializer

class PasswordResetEmailView(generics.GenericAPIView):
    serializer_class = EnterEmailForPasswordResetSerializer
    permission_classes = [AllowAny, ]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')
        user = UserModel.objects.filter(email=email)[0]
        if user:
            token = OTPToken.generate_token(5)
            otpserializer = OTPTokenSerializer(data={"token": token})
            if otpserializer.is_valid():
                otpserializer.save(user=user)
            send_mail(
                "Password reset otp",
                f"password reset token : {token}",
                "from@example.com",
                [email],
                fail_silently=False,
            )

        return Response(
            {"detail": "If an account exists with this email, a reset code has been sent."},
            status=status.HTTP_200_OK
        )
            
class VerifyOTPView(APIView):
    """
    step2: User enters email and OTP to verify
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EnterOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data["otp"]

        try:
            user = UserModel.objects.get(email=email)
            otp_token = OTPToken.objects.filter(user=user).order_by('-created_at').first()

            if not otp_token.is_valid():
                #if otp is expired then delete it.
                otp_token.delete()
                return Response(
                    {'error': 'OTP has expired. Please request a new one.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if otp == otp_token.token:
                reset_token = OTPToken.generate_token(5)
                otp_token.token = reset_token
                otp_token.save()
                return Response(
                    {
                        'message': 'OTP verified successfully.',
                        'reset_token': reset_token
                    },
                    status=status.HTTP_200_OK
                )
        except UserModel.DoesNotExist:
            return Response(
                {
                    'error': 'Invalid credentails.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
class ResetPasswordView(APIView):
    """
    step 3: User sets new password using verified reset token
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CreatePasswordFromResetOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        reset_token = serializer.validated_data["reset_token"]
        new_password = serializer.validated_data["new_password"]

        try:
            user = UserModel.objects.get(email=email)
            otp_token = OTPToken.objects.filter(user=user).filter(token=reset_token).first()

            if not otp_token:
                return Response(
                    {'error': 'Invalid or expired reset token.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not otp_token.is_valid():
                otp_token.delete()
                return Response(
                    {'error': 'Reset token has expired. Please start over.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            print(reset_token, otp_token.token)
            if reset_token != otp_token.token:
                return Response(
                    {'error': 'Invalid reset token.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(new_password)
            user.save()
            otp_token.delete()
            try:
                send_mail(
                    subject='Password Reset Successful',
                    message='Your password has been successfully reset.\n\n'
                            'If you did not perform this action, please contact support immediately.',
                    from_email="from@example.com",
                    recipient_list=[email],
                    fail_silently=True,
                )
            except Exception:
                pass 
            return Response(
                {
                    "detail": "Password successfully changed."
                },
                status=status.HTTP_200_OK
            )

        except UserModel.DoesNotExist:
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_400_BAD_REQUEST
            )

  






