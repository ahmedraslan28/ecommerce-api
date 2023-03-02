from django_filters import FilterSet
from .models import Product


class ProductFilter(FilterSet):
    class Meta:
        model = Product
        fields = {
            'collection': ['exact',],
            'unit_price': ['gt', 'lt']
        }
