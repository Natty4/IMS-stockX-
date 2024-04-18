from django.urls import path
from . import views

urlpatterns = [
    path('stockxuser/create/', views.StockXUserCreateAPIView.as_view(), name='stockxuser-create'),
    path('stockxusers/<str:tg_id>/', views.StockXUserListAPIView.as_view(), name='stockxusers-list'),
    path('storeuser/create/', views.StoreUserCreateAPIView.as_view(), name='storeuser-create'),
    path('storeuser/verify/', views.StoreUserVerificationView.as_view(), name='storeuser-verify'),
    
    path('stores/', views.UserStoreAPIView.as_view(), name='stores'),
    path('stores/create/', views.StoreCreateAPIView.as_view(), name='stores-create'),
    
    path('brands/', views.BrandListAPIView.as_view(), name='brands'),
    path('categories/', views.CategoryListAPIView.as_view(), name='categories'),
    path('size-ranges/', views.SizeRangeListAPIView.as_view(), name='size-ranges'),
    path('colors/', views.ColorListAPIView.as_view(), name='colors'),
    path('products/create/', views.ProductCreateAPIView.as_view(), name='products-create'),
    path('products/', views.ProductListAPIView.as_view(), name='products-list'),
    path('products/<int:pk>/', views.ProductDetailAPIView.as_view(), name='product-detail'),
    path('categories/<int:category>/products/', views.ProductByCategoryListAPIView.as_view(), name='products-by-category'),
    path('products/brand/<int:brand>/', views.ProductByBrandListAPIView.as_view(), name='products-by-brand'),
    
    path('stocks/create/', views.StockCreateAPIView.as_view(), name='stocks-create'),
    path('stocks/update/', views.StockUpdateAPIView.as_view(), name='stocks-update'),
    path('stocks/', views.StockListAPIView.as_view(), name='stocks-list'),
    path('stocks/<int:pk>/', views.StockDetailAPIView.as_view(), name='stock-detail'),
    path('stock-transactions/', views.StockTransactionListAPIView.as_view(), name='stock-transactions'),
    path('sales-transactions/', views.SalesTransactionListAPIView.as_view(), name='sales-transactions'),
    path('sales/create/', views.SalesTransactionCreateAPIView.as_view(), name='sales-create'),
    
    path('reports/', views.ProductPerformanceAPIView.as_view(), name='report'),
]