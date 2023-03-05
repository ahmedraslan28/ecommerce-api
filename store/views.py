from django.http import Http404
from django.shortcuts import get_object_or_404
from django.db.models.aggregates import Count
from django_filters.rest_framework import DjangoFilterBackend

##############################################################

from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import permissions

##############################################################

from . import serializers
from .models import *
from .filters import ProductFilter
from .pagination import DefaultPagination
from .permissions import *


class ProductList(generics.ListCreateAPIView):
    queryset = Product.objects.prefetch_related('images').all()
    serializer_class = serializers.ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    pagination_class = DefaultPagination
    filterset_class = ProductFilter
    search_fields = ['title', 'description']
    ordering_fields = ['unit_price', 'id']
    permission_classes = [IsAdminOrReadOnly]


class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.prefetch_related('images').all()
    serializer_class = serializers.ProductSerializer
    permission_classes = [IsAdminOrReadOnly]

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        if product.orderitems.count() > 0:
            return Response({'error': 'Product cannot be deleted because it is associated with an order item.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CollectionList(generics.ListCreateAPIView):
    queryset = Collection.objects.annotate(
        product_count=Count('products')).all()

    serializer_class = serializers.CollectionSerializer
    permission_classes = [IsAdminOrReadOnly]


class CollectionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Collection.objects.annotate(
        product_count=Count('products')).all()

    serializer_class = serializers.CollectionSerializer
    permission_classes = [IsAdminOrReadOnly]

    def delete(self, request, pk):
        collection = get_object_or_404(Collection, pk=pk)
        if collection.products.count() > 0:
            return Response({'error': 'Collection cannot be deleted because it includes one or more products.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        collection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductReviewList(generics.ListCreateAPIView):
    serializer_class = serializers.ReviewSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        elif self.request.method == 'POST':
            return [permissions.IsAuthenticated()]

    def get_queryset(self):
        product_id = self.kwargs['pk']
        if Product.objects.filter(pk=product_id).exists():
            self.queryset = Review.objects.filter(product=product_id)
            return self.queryset
        raise Http404

    def get_serializer_context(self):
        return {"product_id": self.kwargs["pk"],
                "reviewer_id": self.request.user.id}


class ProductReviewDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.ReviewSerializer

    permission_classes = [IsReviewerOrReadOnly]

    def get_queryset(self):
        self.queryset = Review.objects.filter(
            pk=self.kwargs['pk'], product=self.kwargs['product_id'])
        return self.queryset


class CartCreate(generics.CreateAPIView):
    serializer_class = serializers.CartSerializer
    queryset = Cart.objects.all()


class CartRetrieve(generics.RetrieveDestroyAPIView):
    serializer_class = serializers.CartSerializer
    queryset = Cart.objects.prefetch_related('items__product').all()


class CartItemsList(generics.GenericAPIView):

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.CartItemSerializer
        elif self.request.method == 'POST':
            return serializers.AddCartItemSerializer

    def get_queryset(self):
        if self.queryset is not None:
            return self.queryset
        pk = self.kwargs['pk']
        if Cart.objects.filter(pk=pk).exists():
            self.queryset = CartItem.objects.filter(
                cart_id=pk).select_related('product')
            return self.queryset
        raise Http404()

    def get(self, request, pk):
        obj = self.get_queryset()
        serializer = self.get_serializer(obj, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, pk):
        context = {"cart_id": pk}
        serializer = self.get_serializer(
            data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CartItemDetail(generics.GenericAPIView):
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.CartItemSerializer
        elif self.request.method == 'PATCH':
            return serializers.UpdateCartItemSerializer

    def get(self, request, cart_id, pk):
        obj = get_object_or_404(CartItem, pk=pk, cart_id=cart_id)
        serializer = self.get_serializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, cart_id, pk):
        obj = get_object_or_404(CartItem, pk=pk, cart_id=cart_id)
        serializer = self.get_serializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        obj.quantity = request.data.get('quantity')
        obj.save()
        return Response(serializer.data)

    def delete(self, request, cart_id, pk):
        obj = get_object_or_404(CartItem, pk=pk, cart_id=cart_id)
        obj.delete()
        return Response({"message": "cart item deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class UserRegister(generics.CreateAPIView):
    serializer_class = serializers.UserSerializer
    queryset = None


class CustomerList(generics.ListCreateAPIView):
    serializer_class = serializers.CustomerSerializer
    queryset = Customer.objects.all()
    permission_classes = [permissions.IsAdminUser]


class CustomerDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.CustomerSerializer
    queryset = Customer.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CustomerProfile(generics.GenericAPIView):
    serializer_class = serializers.CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.queryset is not None:
            return self.queryset
        self.queryset = get_object_or_404(Customer, user=self.request.user)
        return self.queryset

    def get(self, request):
        obj = self.get_queryset()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    def put(self, request):
        obj = self.get_queryset()
        serializer = self.get_serializer(
            obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class OrderList(generics.ListCreateAPIView):

    def get_queryset(self):
        if self.queryset is not None:
            return self.queryset
        user = self.request.user
        if user.is_staff:
            self.queryset = Order.objects.prefetch_related(
                'items__product').all()
        else:
            customer_id = Customer.objects.get(user_id=user.id)
            self.queryset = Order.objects.prefetch_related(
                'items__product').filter(customer_id=customer_id)
        return self.queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={'user_id': self.request.user.id})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        serializer = serializers.OrderSerializer(order)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.CreateOrderSerializer
        return serializers.OrderSerializer

    pagination_class = DefaultPagination
    permission_classes = [permissions.IsAuthenticated]


class OrderDetail(generics.RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    queryset = Order.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return serializers.UpdateOrderSerializer
        return serializers.OrderSerializer

    def get_permissions(self):
        if self.request.method in ['PATCH', 'DELETE']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


class ProductImagesList(generics.ListCreateAPIView):
    def get_serializer_context(self):
        return {"product_id": self.kwargs["pk"]}

    serializer_class = serializers.ProductImageSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        if self.queryset is not None:
            return self.queryset
        product_id = self.kwargs["pk"]
        if Product.objects.filter(pk=product_id).exists():
            self.queryset = ProductImage.objects.filter(product_id=product_id)
            return self.queryset
        raise Http404
