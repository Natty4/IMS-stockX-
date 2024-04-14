from rest_framework import generics, status
from rest_framework.response import Response
from django.db.models import Sum
from django.db.models import F
from django.core.exceptions import ValidationError
from .models import Brand, Category, SizeRange, Color, Product, Stock, SalesTransaction, StockTransaction
from .serializers import *

class BrandListAPIView(generics.ListAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer

class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
class SizeRangeListAPIView(generics.ListAPIView):
    queryset = SizeRange.objects.all()
    serializer_class = SizeRangeSerializer
    
class ColorListAPIView(generics.ListAPIView):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
class ProductCreateAPIView(generics.CreateAPIView):
    serializer_class = ProductSerializer
class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer
class ProductDetailAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer

class ProductByCategoryListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        category = self.kwargs['category']
        return Product.objects.filter(category=category)
    
class ProductByBrandListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        brand = self.kwargs['brand']
        return Product.objects.filter(brand=brand)
   

class ProductCreateAPIView(generics.CreateAPIView):
    serializer_class = ProductSerializer
    # if the product intial qunatity is provided, create a stock instance for the product with the initial quantity else create the product without a stock instance
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        initial_quantity = validated_data.get('initial_quantity', 0)
        product = serializer.save()
        
        if initial_quantity > 0:
            Stock.objects.create(product=product, stock_on_hand=initial_quantity, created_by=validated_data['created_by'])
            StockTransaction.objects.create(product=product, quantity=initial_quantity, stock_type='1', modified_by=validated_data['created_by'])
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class StockCreateAPIView(generics.CreateAPIView):
    serializer_class = StockSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        product = validated_data['product']
        quantity = validated_data['stock_on_hand']
        modified_by = validated_data['created_by']

        # Try to retrieve existing stock instance
        try:
            stock = Stock.objects.get(product=product)
            stock.update_stock_on_hand(quantity)
        except Stock.DoesNotExist:
            # Create new stock instance if it doesn't exist
            stock = Stock.objects.create(
                product=product,
                stock_on_hand=quantity,
                created_by=modified_by
            )

        # Create stock transaction
        stock_transaction = StockTransaction.objects.create(
            product=product,
            quantity=quantity,
            stock_type='1',
            modified_by=modified_by
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

class StockUpdateAPIView(generics.UpdateAPIView):
    serializer_class = StockSerializer

    def update(self, request, *args, **kwargs):
        # Extract the product identifier from the request data
        product_id = request.data.get('product')
        
        # Retrieve the stock object using the product identifier
        try:
            stock = Stock.objects.get(product_id=product_id)
        except Stock.DoesNotExist:
            return Response({'error': 'Stock not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Update the stock object with the request data
        # the stock_on_hand field is the only field that can be updated and it should be increamented not replaced
        
        stock.stock_on_hand += int(request.data.get('stock_on_hand'))
        stock.save()
        serializer = self.get_serializer(stock)
        
        
        # Create stock transaction
        quantity = request.data.get('stock_on_hand')
        modified_by = request.data.get('created_by')
        stock_transaction = StockTransaction.objects.create(
            product_id=product_id,
            quantity=quantity,
            stock_type='1',
            modified_by=modified_by
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    

class StockTransactionListAPIView(generics.ListAPIView):
    queryset = StockTransaction.objects.all()
    serializer_class = StockTransactionListSerializer

class StockListAPIView(generics.ListAPIView):
    queryset = Stock.objects.all()
    serializer_class = StockDetailSerializer

class StockDetailAPIView(generics.RetrieveAPIView):
    queryset = Stock.objects.all()
    serializer_class = StockDetailSerializer

class LowStockProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.filter(stock__stock_on_hand__lte=F('low_stock_threshold'))
    serializer_class = ProductSerializer
    
class SalesTransactionCreateAPIView(generics.CreateAPIView):
    serializer_class = SalesTransactionSerializer


    def handle_errors(self, product, quantity_sold):
        try:
            stock = Stock.objects.get(product=product)
        except Stock.DoesNotExist:
            raise ValidationError(f"Stock for product [{product}] does not exist")
        
        if stock.stock_on_hand < quantity_sold:
            raise ValidationError(f"Not enough stock for product [{product}]")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        instance = serializer.validated_data
        product = instance['product']
        quantity_sold = instance['quantity_sold']
        modified_by = instance['sold_by']
        
        try:
            self.handle_errors(product, quantity_sold)
            
            stock_transaction = StockTransaction.objects.create(
                product=product,
                quantity=-quantity_sold,
                stock_type='2',
                modified_by=modified_by
            )
            
            stock = Stock.objects.get(product=product)
            stock.stock_on_hand -= quantity_sold
            stock.save()
            
            serializer.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except ValidationError as error:
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)
    
class SalesTransactionListAPIView(generics.ListAPIView):
    queryset = SalesTransaction.objects.all()
    serializer_class = SalesTransactionListSerializer

class ProductPerformanceAPIView(generics.ListAPIView):
    serializer_class = ProductReportSerializer

    def get_queryset(self):
        try:
            # Calculate total stock in and out
            total_stock_in = StockTransaction.objects.filter(stock_type='1').aggregate(Sum('quantity'))['quantity__sum'] or 0
            total_stock_out = StockTransaction.objects.filter(stock_type='2').aggregate(Sum('quantity'))['quantity__sum'] or 0
            
            # Calculate total stock amount and value
            total_stock_on_hand = total_stock_in - (-1*total_stock_out)
            total_stock_value = total_stock_on_hand * Stock.objects.first().product.cost_price

            # Get best selling product
            # best_selling_product = SalesTransaction.objects.values('product__code').annotate(total_sold=Sum('quantity_sold')).order_by('-total_sold').first()

            # Get list of least selling products with their minimum sold quantities
            least_selling = {}
            best_selling = {}
            product_sales = {}
            all_products = Stock.objects.all()
            all_sales_transactions = SalesTransaction.objects.all()
            for product in all_products:
                product_sales[product.product.code] = 0
            for product in product_sales:
                for sale in all_sales_transactions:
                    if sale.product.code == product:
                        product_sales[product] += sale.quantity_sold
            
            if product_sales:
                sorted_product_sales = dict(sorted(product_sales.items(), key=lambda item: item[1]))
                min_sales = min(sorted_product_sales.values())
                max_sales = max(sorted_product_sales.values())
                
                least_selling_products = [product for product, sales in sorted_product_sales.items() if sales == min_sales]
                best_selling_products = [product for product, sales in sorted_product_sales.items() if sales == max_sales]
                
                least_selling['products'] = least_selling_products
                least_selling['quantity_sold'] = min_sales
                best_selling['products'] = best_selling_products
                best_selling['quantity_sold'] = max_sales
            else:
                least_selling['products'] = []
                least_selling['quantity_sold'] = None
                best_selling['products'] = []
                best_selling['quantity_sold'] = None
            
            return {
                'total_stock_in': total_stock_in,
                'total_stock_out': total_stock_out,
                'total_stock_on_hand': total_stock_on_hand,
                'total_stock_value': total_stock_value,
                'best_selling_product': best_selling,
                'least_selling_product': least_selling
            }
        except Exception as e:
            return {
                'error': str(e)
            }

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if 'error' in queryset:
            return Response(queryset, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)