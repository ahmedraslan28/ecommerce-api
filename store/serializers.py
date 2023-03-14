from django.contrib.auth import get_user_model
from django.db import transaction

from rest_framework import serializers

from decimal import Decimal
from .models import *

User = get_user_model()


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'title', 'product_count']

    product_count = serializers.IntegerField(read_only=True)


class ProductImageSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        product_id = self.context['product_id']
        return ProductImage.objects.create(product_id=product_id, **validated_data)

    class Meta:
        model = ProductImage
        fields = ['id', 'image']


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    uploaded_images = serializers.ListField(
        child=serializers.ImageField(max_length=None,
                                     allow_empty_file=True, use_url=True),
        write_only=True,
        required=False,
        default=[]
    )

    price = serializers.DecimalField(
        max_digits=6, decimal_places=2, source='unit_price')

    price_with_tax = serializers.SerializerMethodField(
        method_name='calculate_tax')

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'slug', 'inventory',
                  'price', 'price_with_tax', 'collection', 'images', 'uploaded_images']

    def calculate_tax(self, instance: Product):
        return instance.unit_price * Decimal(1.1)

    def create(self, validated_data):
        upladed_images = validated_data.pop('uploaded_images')
        product = Product.objects.create(**validated_data)
        image_list = []
        for image in upladed_images:
            image_list.append(
                ProductImage(product=product, image=image)
            )

        ProductImage.objects.bulk_create(image_list)

        return product


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'unit_price']


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'reviewer_id', 'name', 'description', 'rate', 'date']

    def create(self, validated_data):
        return Review.objects.create(
            product_id=self.context['product_id'],
            reviewer_id=self.context['reviewer_id'],
            **validated_data
        )


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer(read_only=True)
    total_price = serializers.SerializerMethodField(
        method_name='calc_price', read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']

    def calc_price(self, instance: CartItem):
        return instance.quantity * instance.product.unit_price


class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                'No product with the given id was found')
        return value

    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'quantity']

    def save(self, **kwargs):

        validated_data = {**self.validated_data}
        cart_id = self.context['cart_id']
        product_id = validated_data['product_id']
        quantity = validated_data['quantity']
        try:
            cart_item = CartItem.objects.get(
                cart_id=cart_id, product_id=product_id)
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item

        except CartItem.DoesNotExist:
            self.instance = CartItem.objects.create(
                cart_id=cart_id, **self.validated_data)

        return self.instance


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(read_only=True, many=True)
    total_price = serializers.SerializerMethodField(
        method_name='calc_price', read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price']

    def calc_price(self, instance: Cart):
        price = 0
        for item in instance.items.all():
            price += item.quantity * item.product.unit_price
        return price


class UserSerializer(serializers.ModelSerializer):
    repeat_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name',
                  'last_name', 'password', 'repeat_password']

    def validate(self, data):
        if data['password'] != data['repeat_password']:
            raise serializers.ValidationError("password do not match")
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('repeat_password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(UserSerializer):
    repeat_password = serializers.CharField(
        write_only=True, allow_blank=True)
    old_password = serializers.CharField(
        write_only=True, allow_blank=True)
    password = serializers.CharField(
        write_only=True, allow_blank=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'first_name',
                  'last_name', 'old_password', 'password', 'repeat_password']

    def validate(self, data):
        super().validate(data)
        user = self.context['user']
        old_password = data['old_password']
        new_password = data['password']
        repeat_password = data['repeat_password']
        if len(old_password) > 0 and not user.check_password(old_password):
            raise serializers.ValidationError("old password is invalid")

        if not (all(len(v) > 0 for v in [old_password, new_password, repeat_password])
                or all(len(v) == 0 for v in [old_password, new_password, repeat_password])):
            raise serializers.ValidationError(
                "please check your passwords fields")
        return data

    def update(self, instance, validated_data):
        old_password = validated_data.pop('old_password')
        new_password = validated_data.pop('password')
        repeat_password = validated_data.pop('repeat_password')
        if all(len(v) > 0 for v in [old_password, new_password, repeat_password]):
            instance.set_password(new_password)
        return super().update(instance, validated_data)


class CustomerSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'user_id', 'phone', 'birth_date', 'membership']


class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'unit_price', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_id = serializers.IntegerField()

    class Meta:
        model = Order
        fields = ['id', 'customer_id', 'placed_at', 'payment_status', 'items']


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, cart_id):
        if not Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError(
                'No cart with the given ID was found.')
        if CartItem.objects.filter(cart_id=cart_id).count() == 0:
            raise serializers.ValidationError('The cart is empty.')
        return cart_id

    def save(self, **kwargs):
        with transaction.atomic():
            validated_data = {**self.validated_data}
            cart_id = validated_data['cart_id']

            customer = Customer.objects.get(
                user_id=self.context['user_id'])

            order = Order.objects.create(customer=customer)

            cart_items = CartItem.objects.select_related(
                'product').filter(cart_id=cart_id)

            order_items = []

            for item in cart_items:
                order_items.append(
                    OrderItem(
                        order=order,
                        product=item.product,
                        unit_price=item.product.unit_price,
                        quantity=item.quantity
                    )
                )

            OrderItem.objects.bulk_create(order_items)

            Cart.objects.filter(pk=cart_id).delete()

            return order


class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['payment_status']


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmationSerializer(serializers.Serializer):
    password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate(self, data):
        super().validate(data)
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError(
                "the two passwords doesn't match!")
        return data
