from django.http import Http404
from django.shortcuts import get_object_or_404
from django.db.models.aggregates import Count
from django_filters.rest_framework import DjangoFilterBackend

##############################################################

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView,
    CreateAPIView, RetrieveDestroyAPIView, ListAPIView)
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter

##############################################################

from .serializers import (
    ProductSerializer, CollectionSerializer, ReviewSerializer,
    CartSerializer, CartItemSerializer, AddCartItemSerializer,
    UpdateCartItemSerializer)
from .models import (Product, Collection, Review, Cart, CartItem)
from .filters import ProductFilter
from .pagination import DefaultPagination


class ProductList(ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    pagination_class = DefaultPagination
    filterset_class = ProductFilter
    search_fields = ['title', 'description']
    ordering_fields = ['unit_price']


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
    queryset = Collection.objects.annotate(
        product_count=Count('products')).all()

    serializer_class = CollectionSerializer

    def delete(self, request, pk):
        collection = get_object_or_404(Collection, pk=pk)
        if collection.products.count() > 0:
            return Response({'error': 'Collection cannot be deleted because it includes one or more products.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        collection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductReviewList(ListCreateAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        product_id = self.kwargs['pk']
        get_object_or_404(Product, pk=product_id)
        return Review.objects.filter(product=product_id)

    def get_serializer_context(self):
        return {"product_id": self.kwargs["pk"]}


class ProductReviewDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(pk=self.kwargs['pk'], product=self.kwargs['product_id'])


class CartCreate(CreateAPIView):
    serializer_class = CartSerializer
    queryset = Cart.objects.all()


class CartRetrieve(RetrieveDestroyAPIView):
    serializer_class = CartSerializer
    queryset = Cart.objects.prefetch_related('items__product').all()


class CartItemsList(APIView):
    def get_queryset(self, pk):
        if Cart.objects.filter(pk=pk).exists():
            return CartItem.objects.filter(cart_id=pk).select_related('product')
        raise Http404()

    def get(self, request, pk):
        obj = self.get_queryset(pk)
        serializer = CartItemSerializer(obj, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, pk):
        context = {"cart_id": pk}
        serializer = AddCartItemSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CartItemDetail(APIView):
    def get(self, request, cart_id, pk):
        obj = get_object_or_404(CartItem, pk=pk, cart_id=cart_id)
        serializer = CartItemSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, cart_id, pk):
        obj = get_object_or_404(CartItem, pk=pk, cart_id=cart_id)
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj.quantity = request.data.get('quantity')
        obj.save()
        return Response(serializer.data)

    def delete(self, request, cart_id, pk):
        obj = get_object_or_404(CartItem, pk=pk, cart_id=cart_id)
        obj.delete()
        return Response({"message": "cart item deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
