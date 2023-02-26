from decimal import Decimal
from rest_framework import serializers
from . models import Product, Collection


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
