from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from store.serializers import OrderCreateSerializer, OrderListSerializer, OrderDetailSerializer, OrderStatusUpdateSerializer
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from rest_framework.permissions import IsAuthenticated
from store.models import Order, CustomUser

class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

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
        except IntegrityError:
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Integrity error occurred.",
                "data": {},
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An unexpected error occurred.",
                "data": str(e),
                "success": False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OrderPagination(PageNumberPagination):
    page_size = 10  # Number of orders per page
    page_size_query_param = 'page_size'
    max_page_size = 100

class OrderListView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    pagination_class = OrderPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        if user_id:
            try:
                user = CustomUser.objects.get(id=user_id)
            except CustomUser.DoesNotExist:
                return Order.objects.none()  # Return an empty queryset if user is not found
            return Order.objects.filter(user=user)
        return Order.objects.all()

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = self.get_serializer(paginated_queryset, many=True)
        return Response({
            "code": status.HTTP_200_OK,
            "message": "Orders retrieved successfully",
            "data": {
                "orders": serializer.data,
                "count": paginator.page.paginator.count
            },
            "success": True
        }, status=status.HTTP_200_OK)
    
class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        try:
            order = Order.objects.get(id=id)
            serializer = OrderDetailSerializer(order)
            return Response({
                "code": status.HTTP_200_OK,
                "message": "Order details retrieved successfully",
                "data": serializer.data,
                "success": True
            }, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "message": "Order not found",
                "success": False
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"An unexpected error occurred: {str(e)}",
                "success": False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OrderStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id, *args, **kwargs):
        try:
            order = Order.objects.get(id=id, user=request.user)
        except Order.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "message": "Order not found or you do not have permission to modify this order.",
                "success": False
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderStatusUpdateSerializer(order, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "code": status.HTTP_200_OK,
                "message": "Order status updated successfully.",
                "data": serializer.data,
                "success": True
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid data",
                "errors": serializer.errors,
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)