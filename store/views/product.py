from rest_framework.pagination import PageNumberPagination
from ..models import Product, Category
from rest_framework.permissions import IsAuthenticated
from ..serializers import ProductSerializer
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView

class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Associate the product with the user who created it
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            response_data = {
                "code": 201,
                "message": "Product successfully created",
                "data": serializer.data,
                "success": True
            }
            return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductPagination(PageNumberPagination):
    page_size = 10  # Default number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 100

class ProductListView(APIView):
    def get(self, request):
        # Filtering parameters
        category_name = request.query_params.get('category')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        
        # Querying the database
        products = Product.objects.all()

        if category_name:
            # Filter by category name, ensure it's a valid Category instance
            category = Category.objects.filter(name=category_name).first()
            if category:
                products = products.filter(category=category)
        if min_price and max_price:
            products = products.filter(price__gte=min_price, price__lte=max_price)
        
        # Pagination
        paginator = ProductPagination()  # Use your custom pagination class
        result_page = paginator.paginate_queryset(products, request)
        
        serializer = ProductSerializer(result_page, many=True)
        
        response_data = {
            'code': 200,
            'message': 'Successfully retrieved all products',
            'data': {
                'products': serializer.data,
                'next': paginator.get_next_link(),  # Pagination metadata
                'previous': paginator.get_previous_link(),  # Pagination metadata
            },
            'success': True
        }
        
        return Response(response_data, status=status.HTTP_200_OK)

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get(self, request, *args, **kwargs):
        try:
            product = self.get_object()
            serializer = self.get_serializer(product)
            return Response({
                'code': 200,
                'message': 'Successfully retrieved single product',
                'data': serializer.data,
                'success': True
            }, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({
                'code': 404,
                'message': 'Product not found',
                'data': {},
                'success': False
            }, status=status.HTTP_404_NOT_FOUND)

class ProductUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    def patch(self, request, pk, format=None):
        product = self.get_object(pk)
        if product is None:
            return Response({
                "code": 404,
                "message": "Product not found",
                "success": False
            }, status=status.HTTP_404_NOT_FOUND)

        if product.created_by != request.user:
            return Response({
                "code": 403,
                "message": "You do not have permission to edit this product.",
                "success": False
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = ProductSerializer(product, data=request.data, partial=True)  # Handle partial updates
        if serializer.is_valid():
            serializer.save()
            return Response({
                "code": 200,
                "message": "Product successfully updated",
                "data": serializer.data,
                "success": True
            }, status=status.HTTP_200_OK)
        return Response({
            "code": 400,
            "message": "Invalid data",
            "data": serializer.errors,
            "success": False
        }, status=status.HTTP_400_BAD_REQUEST)

class ProductDeleteView(generics.DestroyAPIView):
    queryset = Product.objects.all()
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        product_id = kwargs.get('id')
        try:
            product = self.get_queryset().get(id=product_id, created_by=request.user)
        except Product.DoesNotExist:
            return Response({
                "code": 404,
                "message": "Product not found or you don't have permission to delete it.",
                "data": {},
                "success": False
            }, status=status.HTTP_404_NOT_FOUND)

        product.delete()
        return Response({
            "code": 200,
            "message": "Product successfully deleted",
            "data": {},
            "success": True
        }, status=status.HTTP_200_OK)

