from rest_framework import generics, status
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from .models import Product, SalesTransaction, StockTransaction, Color
from .serializers import ProductSerializer, SalesTransactionSerializer, StockTransactionSerializer, ColorSerializer

class ProductListCreateAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['quantity_available'] = serializer.validated_data['initial_quantity']
            self.perform_create(serializer)

            # Create initial stock transaction
            StockTransaction.objects.create(
                product=serializer.instance,
                quantity_added=serializer.instance.intial_quantity
            )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)

            # Create stock transaction
            StockTransaction.objects.create(
                product=instance,
                quantity_added=serializer.validated_data['quantity_available']
            )

            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class SalesTransactionListCreateAPIView(generics.ListCreateAPIView):
    queryset = SalesTransaction.objects.all()
    serializer_class = SalesTransactionSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        # Deduct sold quantity from product's quantity_available
        product = instance.product
        product.quantity_available -= instance.quantity_sold
        product.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                self.perform_create(serializer)
            except ValidationError as e:
                product = serializer.validated_data.get('product')
                available_quantity = product.quantity_available
                requested_quantity = serializer.validated_data.get('quantity_sold')
                error_message = f"The available amount is {available_quantity}, which is {requested_quantity / available_quantity} times less than the requested quantity {requested_quantity}"
                return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SalesTransactionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SalesTransaction.objects.all()
    serializer_class = SalesTransactionSerializer

class StockTransactionListCreateAPIView(generics.ListCreateAPIView):
    queryset = StockTransaction.objects.all()
    serializer_class = StockTransactionSerializer

    def perform_create(self, serializer):
        instance = serializer.save()

        # Add added quantity to product's quantity_available
        product = instance.product
        product.quantity_available += instance.quantity_added
        product.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StockTransactionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = StockTransaction.objects.all()
    serializer_class = StockTransactionSerializer