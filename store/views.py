from django.conf import settings
from django.http import Http404
from django.db.models.aggregates import Count
from django_filters.rest_framework import DjangoFilterBackend
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str

##############################################################

from rest_framework import status
from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.filters import SearchFilter, OrderingFilter

##############################################################

from . import serializers
from .models import *
from .filters import ProductFilter
from .pagination import DefaultPagination
from .permissions import *
from datetime import datetime, timedelta


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
    partial = True

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        if product.orderitems.count() > 0:
            return Response({'error': 'Product cannot be deleted because it is associated with an order item.'},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
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
            return Response({'error': 'Collection cannot be deleted because it includes one or more products.'},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
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

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        response = {
            **serializer.data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        return Response(response)


class UserList(generics.ListAPIView):
    serializer_class = serializers.UserSerializer
    queryset = User.objects.all()
    permission_classes = [permissions.IsAdminUser]


class UserProfile(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return serializers.UserUpdateSerializer
        return serializers.UserSerializer

    def get_queryset(self):
        if self.queryset is not None:
            return self.queryset
        self.queryset = get_object_or_404(User, pk=self.request.user.id)
        return self.queryset

    def get(self, request):
        obj = self.get_queryset()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    def put(self, request):
        obj = self.get_queryset()
        context = {"user": self.request.user}
        serializer = self.get_serializer(
            obj, data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PasswordReset(generics.GenericAPIView):
    serializer_class = serializers.PasswordResetSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            token = default_token_generator.make_token(user)
            reset_url = f"http://localhost:8000//api/auth/reset-password/{uid}/{token}"
            send_mail(
                'Reset Your Password',
                f'Please click on this link to reset your password: {reset_url}',
                settings.EMAIL_HOST_USER,
                [email],
            )
        except User.DoesNotExist:
            return Response({'no user found with given email'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'success': 'Password reset Email sent to the specified email address'})


class PasswordResetConfirmation(generics.GenericAPIView):
    serializer_class = serializers.PasswordResetConfirmationSerializer

    def post(self, request, uidb64, token):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is not None and default_token_generator.check_token(user, token):
            user.set_password(serializer.validated_data['password'])
            user.save()
            return Response({'success': 'Password has been reset.'})
        return Response({'error': 'Invalid reset URL.'})


class CustomerList(generics.ListAPIView):
    serializer_class = serializers.CustomerSerializer
    queryset = Customer.objects.all()
    permission_classes = [permissions.IsAdminUser]


class CustomerDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.CustomerSerializer
    queryset = Customer.objects.all()
    permission_classes = [IsAdminOrReadOnly]


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


class ProductImagesList(generics.ListAPIView):
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


class ProductImageDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.ProductImageSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        if self.queryset is not None:
            return self.queryset
        product_id = self.kwargs["product_pk"]
        image_id = self.kwargs["pk"]
        if Product.objects.filter(pk=product_id).exists():
            self.queryset = ProductImage.objects.filter(
                pk=image_id, product_id=product_id)
            return self.queryset
        raise Http404
