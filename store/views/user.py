from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from ..serializers import SignupSerializer, UserProfileSerializer
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.conf import settings

class SignupView(APIView):
    authentication_classes = []  # Disable authentication for this view
    permission_classes = [AllowAny]  # Allow unauthenticated access

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Send thank you email
            message = "Thank you for signing up to Stephen's Stores"
            send_mail(
                'Thank You for Signing Up',
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return Response({
                "code": 200,
                "message": "Successful signup. Thank you for signing up to Stephen's Stores.",
                "data": {
                    "name": user.name,
                    "phone_number": user.phone_number,
                    "address": user.address,
                    "email": user.email
                },
                "success": True
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({
                "code": 400,
                "message": "Email and password are required",
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(email=email, password=password)

        if user is None:
            return Response({
                "code": 400,
                "message": "Invalid email or password",
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            "code": 200,
            "message": "Login successful",
            "userId": user.id,
            "token": access_token,
            "success": True
        }, status=status.HTTP_200_OK)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            serializer = UserProfileSerializer(user)
            return Response({
                "code": 200,
                "message": "Successfully fetched profile",
                "data": serializer.data,
                "success": True
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "code": 500,
                "message": str(e),
                "success": False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        try:
            user = request.user
            serializer = UserProfileSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "code": 200,
                    "message": "Successfully updated user",
                    "data": serializer.data,
                    "success": True
                }, status=status.HTTP_200_OK)
            return Response({
                "code": 400,
                "message": "Invalid data",
                "errors": serializer.errors,
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "code": 500,
                "message": str(e),
                "success": False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)