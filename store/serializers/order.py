from rest_framework import serializers
from store.models import OrderItem, Product, Order, CustomUser

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price']

class OrderCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    products = serializers.ListField(
        child=serializers.DictField()
    )
    shipping_address = serializers.CharField(max_length=255)
    payment_method = serializers.CharField(max_length=50)

    def validate(self, data):
        errors = {}

        for product_data in data['products']:
            product_id = product_data.get('product_id')
            quantity = product_data.get('quantity')
            price = product_data.get('price')

            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                errors[f'product_{product_id}'] = f"Product with ID {product_id} does not exist."
                continue

            if product.stock_quantity < quantity:
                errors[f'product_{product_id}'] = f"Only {product.stock_quantity} units of {product.name} are available."

            expected_price = product.price * quantity
            if price is not None and price != expected_price:
                errors[f'product_{product_id}_price'] = f"Invalid price for {product.name}. The correct price should be {expected_price:.2f}."

        if data['payment_method'] not in ['Credit Card', 'PayPal', 'Cash on Delivery']:
            errors['payment_method'] = "Invalid payment method."

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        try:
            user = CustomUser.objects.get(id=validated_data['user_id'])
            order = Order.objects.create(
                user=user,
                shipping_address=validated_data['shipping_address'],
                payment_method=validated_data['payment_method'],
            )

            total_price = 0
            for product_data in validated_data['products']:
                product_id = product_data.get('product_id')
                quantity = product_data.get('quantity')
                price = product_data.get('price')

                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    # Handle the case if product is not found
                    raise serializers.ValidationError(f"Product with ID {product_id} does not exist.")

                item_price = product.price * quantity
                total_price += item_price

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=item_price
                )

                product.stock_quantity -= quantity
                product.save()

            order.total_price = total_price
            order.save()

            return order
        except serializers.ValidationError as e:
            # Log validation errors
            print(f"Validation Error: {e}")
            raise
        except Exception as e:
            # Log unexpected errors
            print(f"Unexpected Error: {e}")
            raise

class OrderListSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)  # Nested serializer for order items

    class Meta:
        model = Order
        fields = ['id', 'created_at', 'shipping_address', 'payment_method', 'total_price', 'items']

class OrderItemDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price']

class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'created_at', 'shipping_address', 'payment_method', 'total_price', 'shipping_status', 'items']

class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['shipping_status']

    def validate_shipping_status(self, value):
        if self.instance.shipping_status == 'cancelled':
            raise serializers.ValidationError("Cannot change status of a cancelled order.")
        if self.instance.shipping_status == 'delivered' and value != 'delivered':
            raise serializers.ValidationError("Cannot change status of a delivered order.")
        if self.instance.shipping_status == 'pending' and value not in ['shipped', 'cancelled']:
            raise serializers.ValidationError("Invalid status transition.")
        return value