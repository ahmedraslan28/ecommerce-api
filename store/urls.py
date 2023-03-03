from django.urls import path
from .views import (ProductList, ProductDetail, CollectionList,
                    CollectionDetail, ProductReviewList, ProductReviewDetail,
                    CartCreate, CartRetrieve, CartItemsList, CartItemDetail)
urlpatterns = [
    path('products/', ProductList.as_view(), name="product-list"),
    path('products/<int:pk>/', ProductDetail.as_view(), name="product-detail"),

    path('collections/', CollectionList.as_view(), name="collection-list"),
    path('collections/<int:pk>/', CollectionDetail.as_view(),
         name="collection-detail"),

    path('products/<int:pk>/reviews/',
         ProductReviewList.as_view(), name="product-review-list"),
    path('products/<int:product_id>/reviews/<int:pk>/',
         ProductReviewDetail.as_view(), name="product-review-detail"),

    path('cart/', CartCreate.as_view(), name="cart-create"),
    path('cart/<str:pk>/', CartRetrieve.as_view(), name="cart-detail"),

    path('cart/<str:pk>/items/', CartItemsList.as_view(), name='cartitem-list'),
    path('cart/<str:cart_id>/items/<int:pk>',
         CartItemDetail.as_view(), name='cartitem-detail'),
]
