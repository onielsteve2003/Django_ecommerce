from rest_framework import generics, status
from store.models import Category
from store.serializers import CategorySerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        response_data = {
            "code": 200,
            "message": "Categories retrieved successfully",
            "data": {"categories": serializer.data},
            "success": True
        }
        
        return Response(response_data, status=status.HTTP_200_OK)

class CategoryCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'code': 201,
                'message': 'Category created successfully',
                'data': {},
                'success': True
            }, status=status.HTTP_201_CREATED)
        return Response({
            'code': 400,
            'message': 'Category creation failed',
            'data': serializer.errors,
            'success': False
        }, status=status.HTTP_400_BAD_REQUEST)

class CategoryUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        try:
            # Try to get the category by id and check ownership
            category = Category.objects.get(id=id, created_by=request.user)
        except Category.DoesNotExist:
            return Response({
                'code': 404,
                'message': 'Category not found or you do not have permission to update it',
                'data': {},
                'success': False
            }, status=status.HTTP_404_NOT_FOUND)

        # Initialize the serializer with partial update
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'code': 200,
                'message': 'Category updated successfully',
                'data': serializer.data,
                'success': True
            }, status=status.HTTP_200_OK)
        return Response({
            'code': 400,
            'message': 'Invalid data',
            'data': serializer.errors,
            'success': False
        }, status=status.HTTP_400_BAD_REQUEST)

class CategoryDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        try:
            category = Category.objects.get(id=id, created_by=request.user)
        except Category.DoesNotExist:
            return Response({
                'code': 404,
                'message': 'Category not found or you do not have permission to delete it',
                'data': {},
                'success': False
            }, status=status.HTTP_404_NOT_FOUND)

        # Handle product reassignment logic here if needed
        # For now, we'll just delete the category

        category.delete()
        return Response({
            'code': 200,
            'message': 'Category deleted successfully',
            'data': {},
            'success': True
        }, status=status.HTTP_200_OK)