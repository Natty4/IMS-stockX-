from django.urls import path
from . import views

urlpatterns = [
    path('brands/', views.BrandListAPIView.as_view(), name='brands'),
    path('categories/', views.CategoryListAPIView.as_view(), name='categories'),
    path('size-ranges/', views.SizeRangeListAPIView.as_view(), name='size-ranges'),
    path('colors/', views.ColorListAPIView.as_view(), name='colors'),
    path('products/create/', views.ProductCreateAPIView.as_view(), name='products-create'),
    path('products/', views.ProductListAPIView.as_view(), name='products-list'),
    path('products/<int:pk>/', views.ProductDetailAPIView.as_view(), name='product-detail'),
    path('categories/<int:category>/products/', views.ProductByCategoryListAPIView.as_view(), name='products-by-category'),
    path('products/brand/<int:brand>/', views.ProductByBrandListAPIView.as_view(), name='products-by-brand'),
    
    path('stocks/', views.StockCreateAPIView.as_view(), name='stocks'),
    path('stocks/update/', views.StockUpdateAPIView.as_view(), name='stocks-update'),
    path('stocks-list/', views.StockListAPIView.as_view(), name='stocks-list'),
    path('stocks/<int:pk>/', views.StockDetailAPIView.as_view(), name='stock-detail'),
    path('stocks/low-stock/', views.LowStockProductListAPIView.as_view(), name='low-stock'),
    path('stock-transactions/', views.StockTransactionListAPIView.as_view(), name='stock-transactions'),
    path('sales-transactions/', views.SalesTransactionListAPIView.as_view(), name='sales-transactions'),
    # path('sales-transactions/<int:pk>/', views.SalesTransactionDetailAPIView.as_view(), name='sales-transaction-detail'),
    path('sales/', views.SalesTransactionCreateAPIView.as_view(), name='sales'),
    
    path('reports/low-stock/', views.LowStockProductListAPIView.as_view(), name='low-stock-report'),
    path('reports/', views.ProductPerformanceAPIView.as_view(), name='report'),
]