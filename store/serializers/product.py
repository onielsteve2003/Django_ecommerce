from rest_framework import serializers
from store.models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock_quantity', 'category', 'image']
        extra_kwargs = {
            'name': {'required': True},
            'description': {'required': True},
            'price': {'required': True},
            'stock_quantity': {'required': True},
            'category': {'required': True},
            'image': {'required': True}
        }

    def validate(self, data):
        if 'price' in data and data['price'] <= 0:
            raise serializers.ValidationError({'price': 'Price must be greater than zero.'})
        if 'stock_quantity' in data and data['stock_quantity'] < 0:
            raise serializers.ValidationError({'stock_quantity': 'Stock quantity cannot be negative.'})
        return data
