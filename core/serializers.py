from rest_framework import serializers
from .models import Product, SalesTransaction, StockTransaction, Color, Category, SizeRange

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        
class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = '__all__'
        
class SizeRangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeRange
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    colors = ColorSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    size_range = SizeRangeSerializer()
    

    class Meta:
        model = Product
        exclude = ('is_active','created_by','created_at','updated_at', 'barcode', 'image_url')

    def create(self, validated_data):
        colors_data = validated_data.pop('colors', [])
        product = Product.objects.create(**validated_data)
        for color_data in colors_data:
            color, _ = Color.objects.get_or_create(**color_data)
            product.colors.add(color)
        return product

    def update(self, instance, validated_data):
        colors_data = validated_data.pop('colors', [])
        instance = super().update(instance, validated_data)
        instance.colors.clear()
        for color_data in colors_data:
            color, _ = Color.objects.get_or_create(**color_data)
            instance.colors.add(color)
        return instance

class SalesTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesTransaction
        fields = '__all__'

class StockTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockTransaction
        fields = '__all__'
