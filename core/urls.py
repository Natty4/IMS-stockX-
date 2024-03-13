from django.urls import path
from .views import (
    ProductListCreateAPIView,
    ProductDetailAPIView,
    SalesTransactionListCreateAPIView,
    SalesTransactionDetailAPIView,
    StockTransactionListCreateAPIView,
    StockTransactionDetailAPIView
)

urlpatterns = [
     # Product endpoints
    path('products/', ProductListCreateAPIView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductDetailAPIView.as_view(), name='product-detail'),

    # SalesTransaction endpoints
    path('sales-transactions/', SalesTransactionListCreateAPIView.as_view(), name='sales-transaction-list-create'),
    path('sales-transactions/<int:pk>/', SalesTransactionDetailAPIView.as_view(), name='sales-transaction-detail'),

    # StockTransaction endpoints
    path('stock-transactions/', StockTransactionListCreateAPIView.as_view(), name='stock-transaction-list-create'),
    path('stock-transactions/<int:pk>/', StockTransactionDetailAPIView.as_view(), name='stock-transaction-detail'),

]