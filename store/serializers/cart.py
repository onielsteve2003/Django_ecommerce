from rest_framework import serializers
from store.models import CartItem

class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity']
    
    def validate(self, data):
        product = data['product']
        quantity = data['quantity']
        
        if quantity > product.stock_quantity:
            raise serializers.ValidationError("Product out of quantity.")
        
        return data

    def create(self, validated_data):
        cart = validated_data.get('cart')
        product = validated_data.get('product')
        quantity = validated_data.get('quantity')

        # Check if the product is already in the cart
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        if not created:
            # Update the quantity if already exists
            cart_item.quantity += quantity

            if cart_item.quantity > product.stock_quantity:
                raise serializers.ValidationError("Product out of quantity.")
        else:
            cart_item.quantity = quantity
        
        cart_item.save()
        return cart_item
