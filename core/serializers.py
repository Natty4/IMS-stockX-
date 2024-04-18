from rest_framework import serializers
from .models import StockXUser, StoreUser, Store, Product, Stock, SalesTransaction, StockTransaction, Color, Category, SizeRange, Brand

class StockXUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockXUser
        exclude = ['created_at', 'updated_at', 'is_active']
        
class StoreUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreUser
        exclude = ['verified', 'verification_code', 'created_at', 'updated_at']
class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        exclude = ['created_at', 'updated_at']

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class SizeRangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeRange
        fields = ['id', 'name', 'size_value']

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['id', 'name', 'color_code']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        exclude = ['created_at', 'updated_at', 'is_active']

class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    brand = BrandSerializer()
    colors = ColorSerializer(many=True)

    class Meta:
        model = Product
        exclude = ['created_at', 'updated_at', 'is_active']

class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    brand = BrandSerializer()
    size_range = SizeRangeSerializer()
    colors = ColorSerializer(many=True)

    class Meta:
        model = Product
        fields = '__all__'
        
class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = '__all__'

class SalesTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesTransaction
        fields = '__all__'

class StockTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockTransaction
        fields = '__all__'

class SalesTransactionListSerializer(serializers.ModelSerializer):
    product = ProductListSerializer()

    class Meta:
        model = SalesTransaction
        fields = '__all__'

class StockTransactionListSerializer(serializers.ModelSerializer):
    product = ProductListSerializer()

    class Meta:
        model = StockTransaction
        fields = '__all__'

class StockDetailSerializer(serializers.ModelSerializer):
    product = ProductListSerializer()

    class Meta:
        model = Stock
        fields = '__all__'

class LowStockProductDetailSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = Stock
        fields = '__all__'

class ProductReportSerializer(serializers.Serializer):
    total_stock_in = serializers.IntegerField()
    total_stock_out = serializers.IntegerField()
    total_stock_on_hand = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    best_selling_product = serializers.DictField(child=serializers.CharField())
    least_selling_product = serializers.DictField(child=serializers.CharField())