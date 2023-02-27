from django.shortcuts import get_object_or_404
from django.db.models.aggregates import Count
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from .models import Product, Collection
from .serializers import ProductSerializer, CollectionSerializer
# Create your views here.


class ProductList(ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductDetail(RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        if product.orderitems.count() > 0:
            return Response({'error': 'Product cannot be deleted because it is associated with an order item.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CollectionList(ListCreateAPIView):
    queryset = Collection.objects.annotate(
        product_count=Count('products')).all()

    serializer_class = CollectionSerializer


class CollectionDetail(RetrieveUpdateDestroyAPIView):
    queryset = queryset = Collection.objects.annotate(
        product_count=Count('products')).all()

    serializer_class = CollectionSerializer

    def delete(self, request, pk):
        collection = get_object_or_404(Collection, pk=pk)
        if collection.products.count() > 0:
            return Response({'error': 'Collection cannot be deleted because it includes one or more products.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        collection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductReviewList(ListCreateAPIView):
    pass


class ProductReviewDetail(RetrieveUpdateDestroyAPIView):
    pass
