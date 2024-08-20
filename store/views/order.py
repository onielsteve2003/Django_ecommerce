from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from store.serializers import OrderCreateSerializer
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

class OrderCreateView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            serializer = OrderCreateSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "code": status.HTTP_201_CREATED,
                    "message": "Order successfully created",
                    "data": {},
                    "success": True
                }, status=status.HTTP_201_CREATED)
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to create order",
                "data": serializer.errors,
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "message": str(e),
                "data": {},
                "success": False
            }, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError as e:
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Integrity error occurred.",
                "data": str(e),
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An unexpected error occurred.",
                "data": str(e),
                "success": False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
