from django.contrib import admin
from .models import Brand, Category, SizeRange, Color, Product, StockTransaction, SalesTransaction
# Register your models here.


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category', 'brand', 'initial_quantity', 'quantity_available', 'cost_price', 'selling_price']
    search_fields = ['name', 'code', 'brand__name', 'category__name']
    list_filter = ['category', 'brand', 'size_range', 'supplier', 'location']
    list_per_page = 10
    # list_editable = ['cost_price', 'selling_price', 'quantity', 'quantity_available']
    readonly_fields = ['quantity_available']
    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'code', 'description', 'category', 'brand', 'size_range', 'colors', 'barcode', 'image_url')
        }),
        ('Pricing Information', {
            'fields': ('cost_price', 'selling_price')
        }),
        ('Stock Information', {
            'fields': ('initial_quantity', 'quantity_available')
        })
    )
    filter_horizontal = ['colors']
    autocomplete_fields = ['category', 'brand']
    ordering = ['name']


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_code']
    search_fields = ['name', 'color_code']
    list_filter = ['name', ]
    list_per_page = 10
    # list_editable = ['color_code']
    fieldsets = (
        ('Color Information', {
            'fields': ('name', 'color_code')
        }),
    )
    ordering = ['name']


@admin.register(SizeRange)
class SizeRangeAdmin(admin.ModelAdmin):
    list_display = ['name', 'size_value']
    search_fields = ['name', 'size_value']
    list_filter = ['name', 'size_value']
    list_per_page = 10
    fieldsets = (
        ('Size Range Information', {
            'fields': ('name', 'size_value')
        }),
    )
    ordering = ['name']
    
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    list_per_page = 10
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
    list_per_page = 10
    fieldsets = (
        ('Brand Information', {
            'fields': ('name',)
        }),
    )
    ordering = ['name']
    
    
@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity_added', 'stock_date', 'added_by']
    search_fields = ['product__name', 'product__code']
    list_filter = ['stock_date', 'added_by']
    list_per_page = 10
    fieldsets = (
        ('Stock Transaction Information', {
            'fields': ('product', 'quantity_added', 'added_by')
        }),
    )
    ordering = ['stock_date']
    
@admin.register(SalesTransaction)
class SalesTransactionAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity_sold', 'sale_date', 'soled_by']
    search_fields = ['product__name', 'product__code']
    list_filter = ['sale_date', 'soled_by']
    list_per_page = 10
    fieldsets = (
        ('Sales Transaction Information', {
            'fields': ('product', 'quantity_sold', 'soled_by')
        }),
    )
    ordering = ['sale_date']