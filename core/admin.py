from django.contrib import admin
from .models import Brand, Category, SizeRange, Color, Product, Stock, StockTransaction, SalesTransaction

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category', 'brand', 'initial_quantity', 'cost_price', 'selling_price', 'is_active', 'low_stock_threshold']
    search_fields = ['name', 'code', 'brand__name', 'category__name']
    list_filter = ['category', 'brand', 'supplier', 'location']
    list_per_page = 15
    readonly_fields = ['created_by']
    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'code', 'description', 'category', 'brand', 'size_range', 'colors', 'barcode', 'image_url', 'low_stock_threshold', 'is_active')
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


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_code']
    search_fields = ['name', 'color_code']
    list_per_page = 15
    fieldsets = (
        ('Color Information', {
            'fields': ('name', 'color_code')
        }),
    )
    ordering = ['-created_at']


@admin.register(SizeRange)
class SizeRangeAdmin(admin.ModelAdmin):
    list_display = ['name', 'size_value']
    search_fields = ['name', 'size_value']
    list_per_page = 15
    fieldsets = (
        ('Size Range Information', {
            'fields': ('name', 'size_value')
        }),
    )
    ordering = ['-created_at']
    
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    list_per_page = 15
    fieldsets = (
        ('Category Information', {
            'fields': ('name',)
        }),
    )
    ordering = ['name']
    
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    list_per_page = 15
    fieldsets = (
        ('Brand Information', {
            'fields': ('name',)
        }),
    )
    ordering = ['name']
    
    
@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'stock_on_hand', 'created_at', 'updated_at']
    search_fields = ['product__name', 'product__code']
    list_filter = ['created_at', 'updated_at']
    list_per_page = 15
    ordering = ['-updated_at']
    
@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'stock_date', 'modified_by', 'stock_type']
    search_fields = ['product__name', 'product__code']
    list_filter = ['stock_date', 'modified_by', 'stock_type']
    list_per_page = 15
    ordering = ['-stock_date']
    
@admin.register(SalesTransaction)
class SalesTransactionAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity_sold', 'total_amount', 'sold_by']
    search_fields = ['product__name', 'product__code']
    list_filter = ['created_at', 'product__code', 'sold_by']
    list_per_page = 15
    ordering = ['-created_at']  