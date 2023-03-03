from decimal import Decimal
from rest_framework import serializers
from . models import Product, Collection, Review, Cart, CartItem


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'title', 'product_count']

    product_count = serializers.IntegerField(read_only=True)


class ProductSerializer(serializers.ModelSerializer):

    price = serializers.DecimalField(
        max_digits=6, decimal_places=2, source='unit_price')

    price_with_tax = serializers.SerializerMethodField(
        method_name='calculate_tax')

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'slug', 'inventory',
                  'price', 'price_with_tax', 'collection']

    def calculate_tax(self, instance: Product):
        return instance.unit_price * Decimal(1.1)


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'unit_price']


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'name', 'description', 'rate',  'date']

    def create(self, validated_data):
        return Review.objects.create(
            product_id=self.context['product_id'], **validated_data)


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
        print(cart_id, " a7a ", quantity, " a7a ", product_id)
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
