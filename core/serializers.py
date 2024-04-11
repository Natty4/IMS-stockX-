from rest_framework import serializers
from .models import Product, Stock, SalesTransaction, StockTransaction, Color, Category, SizeRange, Brand

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        exclude = ['created_at', 'updated_at']
        
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        exclude = ['created_at', 'updated_at']
        
class SizeRangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeRange
        exclude = ['created_at', 'updated_at']
        
class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        exclude = ['created_at', 'updated_at']
        
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        exclude = ['created_at', 'updated_at', 'is_active']
        
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
    product = ProductSerializer()

    class Meta:
        model = SalesTransaction
        fields = '__all__'
        
class LowStockProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    
    class Meta:
        model = Stock
        fields = '__all__'
        
class StockTransactionListSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    class Meta:
        model = StockTransaction
        fields = '__all__'
        
class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    brand = BrandSerializer()
    size_range = SizeRangeSerializer()
    colors = ColorSerializer(many=True)
    class Meta:
        model = Product
        fields = '__all__'
        
class StockDetailSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    
    class Meta:
        model = Stock
        fields = '__all__'
        
class SalesTransactionDetailSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    
    class Meta:
        model = SalesTransaction
        fields = '__all__'
        
class StockTransactionDetailSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    
    class Meta:
        model = StockTransaction
        fields = '__all__'
        
class LowStockProductDetailSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    
    class Meta:
        model = Stock
        fields = '__all__'
        
class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        
    def create(self, validated_data):
        colors_data = validated_data.pop('colors')
        product = Product.objects.create(**validated_data)
        for color_data in colors_data:
            color = Color.objects.get(pk=color_data['id'])
            product.colors.add(color)
        return product
    
    def update(self, instance, validated_data):
        colors_data = validated_data.pop('colors')
        instance = super().update(instance, validated_data)
        instance.colors.clear()
        for color_data in colors_data:
            color = Color.objects.get(pk=color_data['id'])
            instance.colors.add(color)
        return instance
    

class ProductReportSerializer(serializers.Serializer):
    total_stock_in = serializers.IntegerField()
    total_stock_out = serializers.IntegerField()
    total_stock_on_hand = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    best_selling_product = serializers.DictField(child=serializers.CharField())
    least_selling_product = serializers.DictField(child=serializers.CharField())