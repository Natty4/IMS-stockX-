from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum
from django.db.models import F
from django.core.exceptions import ValidationError
from .models import StockXUser
from .models import StockXUser,StoreUser, Brand, Category, SizeRange, Color, Store, Product, Stock, SalesTransaction, StockTransaction
from .serializers import *


class StockXUserCreateAPIView(generics.CreateAPIView):
    serializer_class = StockXUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# get specific user by tg_id get the id from the url
class StockXUserListAPIView(generics.ListAPIView):
    serializer_class = StockXUserSerializer
    queryset = StockXUser.objects.all()

    def get_queryset(self):
        tg_id = self.kwargs.get('tg_id')
        return StockXUser.objects.filter(tg_id=tg_id)
     
class StoreUserCreateAPIView(generics.CreateAPIView):
    serializer_class = StoreUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Generate verification code
        store_user = serializer.save(verification_code=StoreUser.generate_verification_code(self))

        # Send verification code to user (via Telegram bot or other means)
        # Example: send_verification_code(store_user.user, store_user.verification_code)

        return Response(f"User: {store_user.user} Verification code: {store_user.verification_code}", status=status.HTTP_201_CREATED)

class StoreUserVerificationView(APIView):
    def post(self, request):
        verification_code = request.data.get('verification_code')
        store_user_id = request.data.get('store_user_id')

        try:
            store_user = StoreUser.objects.get(id=store_user_id)
            if store_user.verification_code == verification_code:
                store_user.is_verified = True
                store_user.save()
                return Response({"message": "Store user verified successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid verification code."}, status=status.HTTP_400_BAD_REQUEST)
        except StoreUser.DoesNotExist:
            return Response({"error": "Store user not found."}, status=status.HTTP_404_NOT_FOUND)
 
class UserStoreAPIView(generics.ListAPIView):
    serializer_class = StoreSerializer

    def get_queryset(self):
        default_user = {'tg_id': '441609134', 'first_name': 'admin', 'last_name': 'admin'}
        user = self.request.data.get('user', default_user)
        # Filter store based on the Telegram user ID provided in the request
        return Store.objects.filter(owner__tg_id=user['tg_id'])
    
class StoreCreateAPIView(generics.CreateAPIView):
    serializer_class = StoreSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        store = serializer.save()
        default_user = {'tg_id': '441609134', 'first_name': 'admin', 'last_name': 'admin'}
        user = request.data.get('user', default_user)
        # Associate store with the Telegram user ID provided in the request
        store.owner = StockXUser.objects.filter(tg_id=user['tg_id']).first()
        store.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        initial_quantity = validated_data.get('initial_quantity', 0)
        low_stock_threshold = validated_data.get('low_stock_threshold', 1)
        product = serializer.save()
        default_user = {'tg_id': '441609134', 'first_name': 'admin', 'last_name': 'admin'}
        user = request.data.get('user', default_user)
        # Filter products based on the Telegram user ID provided in the request
        store = Store.objects.filter(owner__tg_id=user['tg_id']).first()
        if not store:
            return Response({'error': 'Store not found for the provided user ID'}, status=status.HTTP_404_NOT_FOUND)

        if initial_quantity > 0:
            Stock.objects.create(store=store, product=product, stock_on_hand=initial_quantity, low_stock_threshold=low_stock_threshold, created_by=user['first_name'])
            StockTransaction.objects.create(store=store, product=product, quantity=initial_quantity, stock_type='1', modified_by=user['first_name'])
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductListSerializer

    def get_queryset(self):
        default_user = {'tg_id': '441609134', 'first_name': 'admin', 'last_name': 'admin'}
        user = self.request.data.get('user', default_user)
        # Filter products based on the Telegram user ID provided in the request
        return Product.objects.filter(store__owner__tg_id=user['tg_id'])

class ProductDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ProductDetailSerializer

    def get_queryset(self):
        default_user = {'tg_id': '441609134', 'first_name': 'admin', 'last_name': 'admin'}
        user = self.request.data.get('user', default_user)
        # Filter products based on the Telegram user ID provided in the request
        return Product.objects.filter(store__owner__tg_id=user['tg_id'])
class ProductByCategoryListAPIView(generics.ListAPIView):
    serializer_class = ProductListSerializer

    def get_queryset(self):
        default_user = {'tg_id': '441609134', 'first_name': 'admin', 'last_name': 'admin'}
        user = self.request.data.get('user', default_user)
        # Filter products by category based on the category ID provided in the URL
        category_id = self.kwargs['category']
        return Product.objects.filter(category_id=category_id, store__owner__tg_id=user['tg_id'])

class ProductByBrandListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        default_user = {'tg_id': '441609134', 'first_name': 'admin', 'last_name': 'admin'}
        user = self.request.data.get('user', default_user)
        # Filter products by brand based on the brand ID provided in the URL
        brand_id = self.kwargs['brand']
        return Product.objects.filter(brand_id=brand_id, store__owner__tg_id=user['tg_id'])
class StockCreateAPIView(generics.CreateAPIView):
    serializer_class = StockSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        product = validated_data['product']
        quantity = validated_data['stock_on_hand']
        
        default_user = {'tg_id': '441609134', 'first_name': 'admin', 'last_name': 'admin'}
        user = request.data.get('user', default_user)
        user_store = Store.objects.filter(owner__tg_id=user['tg_id']).first()
        
        if not user_store:
            return Response({'error': 'Store not found for the provided user ID'}, status=status.HTTP_404_NOT_FOUND)
        if not Product.objects.filter(store=user_store, id=product.id).exists():
            return Response({'error': 'Product not found in the user store'}, status=status.HTTP_404_NOT_FOUND)
        
        # Try to retrieve existing stock instance
        try:
            stock = Stock.objects.get(product=product)
            stock.update_stock_on_hand(quantity)
        except Stock.DoesNotExist:
            # Create new stock instance if it doesn't exist
            stock = Stock.objects.create(
                product=product,
                stock_on_hand=quantity,
                created_by=user['tg_id'],
                store=user_store
            )

        # Create stock transaction
        StockTransaction.objects.create(
            product=product,
            quantity=quantity,
            stock_type='1',
            modified_by=user['tg_id'],
            store=user_store
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class StockUpdateAPIView(generics.UpdateAPIView):
    serializer_class = StockSerializer

    def update(self, request, *args, **kwargs):
        # Extract the product identifier from the request data
        product_id = request.data.get('product')
        default_user = {'tg_id': '441609134', 'first_name': 'admin', 'last_name': 'admin'}
        user = request.data.get('user', default_user)
        user_store = Store.objects.filter(owner__tg_id=user['tg_id']).first()
        if not user_store:
            return Response({'error': 'Store not found for the provided user ID'}, status=status.HTTP_404_NOT_FOUND)
        
        # Retrieve the stock object using the product identifier
        try:
            stock = Stock.objects.get(product_id=product_id, store=user_store)
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
            store=user_store,
            product_id=product_id,
            quantity=quantity,
            stock_type='1',
            modified_by=modified_by
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

class StockTransactionListAPIView(generics.ListAPIView):
    serializer_class = StockTransactionListSerializer

    def get_queryset(self):
        default_user = {'tg_id': '441609134', 'first_name': 'admin', 'last_name': 'admin'}
        user = self.request.data.get('user', default_user)
        # Filter stock transactions based on the Telegram user ID provided in the request
        return StockTransaction.objects.filter(product__store__owner__tg_id=user['tg_id'])

class StockListAPIView(generics.ListAPIView):
    serializer_class = StockDetailSerializer

    def get_queryset(self):
        default_user = {'tg_id': '441609134', 'first_name': 'admin', 'last_name': 'admin'}
        user = self.request.data.get('user', default_user)
        # Filter stock based on the Telegram user ID provided in the request
        return Stock.objects.filter(product__store__owner__tg_id=user['tg_id'])

class StockDetailAPIView(generics.RetrieveAPIView):
    serializer_class = StockDetailSerializer

    def get_queryset(self):
        default_user = {'tg_id': '441609134', 'first_name': 'admin', 'last_name': 'admin'}
        user = self.request.data.get('user', default_user)
        # Filter stock based on the Telegram user ID provided in the request
        return Stock.objects.filter(product__store__owner__tg_id=user['tg_id'])
    
class SalesTransactionCreateAPIView(generics.CreateAPIView):
    serializer_class = SalesTransactionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        product = validated_data['product']
        quantity_sold = validated_data['quantity_sold']

        default_user = {'tg_id': '441609134', 'first_name': 'tester', 'last_name': 'admin'}
        user = self.request.data.get('user', default_user)
        # Filter sales transactions based on the Telegram user ID provided in the request
        user_store = Store.objects.filter(owner__tg_id=user['tg_id']).first()
        if not user_store:
            return Response({'error': 'Store not found for the provided user ID'}, status=status.HTTP_404_NOT_FOUND)
        store = user_store

        try:
            self.handle_errors(product, quantity_sold)
            
            # Create stock transaction
            StockTransaction.objects.create(
                store=store,
                product=product,
                quantity=-quantity_sold,
                stock_type='2',
                modified_by=user['tg_id']
            )
            
            # Update stock on hand
            stock = Stock.objects.get(product=product, store=store)
            stock.stock_on_hand -= quantity_sold
            stock.save()
            serializer.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except ValidationError as error:
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)

    def handle_errors(self, product, quantity_sold):
        try:
            stock = Stock.objects.get(product=product)
        except Stock.DoesNotExist:
            raise ValidationError(f"Stock for product [{product}] does not exist")
        
        if stock.stock_on_hand < quantity_sold:
            raise ValidationError(f"Not enough stock for product [{product}]")

class SalesTransactionListAPIView(generics.ListAPIView):
    serializer_class = SalesTransactionListSerializer

    def get_queryset(self):
        default_user = {'tg_id': '441609134', 'first_name': 'admin', 'last_name': 'admin'}
        user = self.request.data.get('user', default_user)
        # Filter sales transactions based on the Telegram user ID provided in the request
        return SalesTransaction.objects.filter(product__store__owner__tg_id=user['tg_id'])

class ProductPerformanceAPIView(generics.ListAPIView):
    serializer_class = ProductReportSerializer

    def get_queryset(self):
        default_user = {'tg_id': '441609134', 'first_name': 'admin', 'last_name': 'admin'}
        user = self.request.data.get('user', default_user)
        user_store = Store.objects.filter(owner__tg_id=user['tg_id']).first()
        try:
            # Calculate total stock in and out
            total_stock_in = StockTransaction.objects.filter(store=user_store, stock_type='1').aggregate(Sum('quantity'))['quantity__sum'] or 0
            total_stock_out = StockTransaction.objects.filter(store=user_store, stock_type='2').aggregate(Sum('quantity'))['quantity__sum'] or 0
            
            # Calculate total stock amount and value
            total_stock_on_hand = total_stock_in - (-1*total_stock_out)
            total_stock_value = total_stock_on_hand * Stock.objects.first().product.cost_price

            # Get best selling product
            # best_selling_product = SalesTransaction.objects.values('product__code').annotate(total_sold=Sum('quantity_sold')).order_by('-total_sold').first()

            # Get list of least selling products with their minimum sold quantities
            least_selling = {}
            best_selling = {}
            product_sales = {}
            all_products = Stock.objects.filter(store=user_store)
            all_sales_transactions = SalesTransaction.objects.filter(store=user_store)
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