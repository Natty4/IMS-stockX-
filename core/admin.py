from django.contrib import admin
from .models import StockXUser, StoreUser, Brand, Category, SizeRange, Color, Store, Product, Stock, StockTransaction, SalesTransaction


@admin.register(StockXUser)
class StockXUserAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'tg_id', 'email', 'is_active']
    search_fields = ['first_name', 'last_name', 'tg_id', 'email']
    list_per_page = 15
    ordering = ['first_name']
    
@admin.register(StoreUser)
class StoreUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'store', 'role', 'verified']
    search_fields = ['user__first_name', 'user__last_name', 'store__name', 'role']
    list_per_page = 15
    ordering = ['-created_at']
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    list_per_page = 15
    ordering = ['name']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    list_per_page = 15
    ordering = ['name']

@admin.register(SizeRange)
class SizeRangeAdmin(admin.ModelAdmin):
    list_display = ['name', 'size_value']
    search_fields = ['name', 'size_value']
    list_per_page = 15
    ordering = ['-created_at']

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_code']
    search_fields = ['name', 'color_code']
    list_per_page = 15
    ordering = ['-created_at']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category', 'brand', 'initial_quantity', 'cost_price', 'selling_price', 'is_active', 'low_stock_threshold']
    search_fields = ['name', 'code', 'brand__name', 'category__name']
    list_filter = ['category', 'brand', 'supplier', 'store']  # Include 'store' in list_filter
    list_per_page = 15
    readonly_fields = ['created_by']
    fieldsets = (
        ('Product Information', {
            'fields': ('store', 'name', 'code', 'description', 'category', 'brand', 'size_range', 'colors', 'barcode', 'image_url', 'initial_quantity', 'low_stock_threshold', 'is_active')
        }),
        ('Pricing Information', {
            'fields': ('cost_price', 'selling_price')
        }),
        ('Other Information', {
            'fields': ('created_by',)
        })
    )
    filter_horizontal = ['colors']
    autocomplete_fields = ['category', 'brand']
    ordering = ['-updated_at']

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'stock_on_hand', 'created_at', 'updated_at']
    search_fields = ['product__name', 'product__code']
    list_filter = ['created_at', 'updated_at', 'product__store']  # Include 'product__store' in list_filter
    list_per_page = 15
    ordering = ['-updated_at']

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'stock_date', 'modified_by', 'stock_type']
    search_fields = ['product__name', 'product__code']
    list_filter = ['stock_date', 'modified_by', 'stock_type', 'product__store']  # Include 'product__store' in list_filter
    list_per_page = 15
    ordering = ['-stock_date']

@admin.register(SalesTransaction)
class SalesTransactionAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity_sold', 'total_amount', 'sold_by']
    search_fields = ['product__name', 'product__code']
    list_filter = ['created_at', 'product__code', 'sold_by', 'product__store']  # Include 'product__store' in list_filter
    list_per_page = 15
    ordering = ['-created_at']

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'location', 'created_at', 'updated_at']
    search_fields = ['name', 'owner', 'location']
    list_per_page = 15
    ordering = ['-updated_at']