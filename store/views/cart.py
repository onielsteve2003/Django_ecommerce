from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from store.models import Cart
from store.serializers import CartItemSerializer
from store.models import Product

class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "message": "Product not found.",
                "success": False
            }, status=status.HTTP_404_NOT_FOUND)

        # Get or create the cart for the user
        cart, created = Cart.objects.get_or_create(user=user)

        data = {
            'cart': cart.id,
            'product': product.id,
            'quantity': quantity,
        }

        serializer = CartItemSerializer(data=data)
        if serializer.is_valid():
            serializer.save(cart=cart)
            return Response({
                "code": status.HTTP_200_OK,
                "message": "Product added to cart successfully.",
                "data": serializer.data,
                "success": True
            }, status=status.HTTP_200_OK)
        else:
            error_message = list(serializer.errors.values())[0][0]
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message": error_message,
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)