from django.db import models
from django.db.models import Sum
from django.core.validators import RegexValidator
from django.utils.crypto import get_random_string

phone_number_validator = RegexValidator(
    regex=r'^(\+2519\d{8}|\+2517\d{8}|09\d{8}|07\d{8})$',
    message='Phone number must be in the format +2519XXXXXXXX, +2517XXXXXXXX, 09XXXXXXXX, or 07XXXXXXXX'
    
)

class StockXUser(models.Model):
    tg_id = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=15, validators=[phone_number_validator], null=True, blank=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.tg_id})'
    
class Brand(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class SizeRange(models.Model):
    name = models.CharField(max_length=100)
    size_value = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.size_value}"

class Color(models.Model):
    name = models.CharField(max_length=100)
    color_code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Store(models.Model):
    owner = models.ForeignKey(StockXUser, on_delete=models.CASCADE)  # Associate store with a custom user
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class StoreUser(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    user = models.ForeignKey(StockXUser, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)  # e.g., "Store Owner", "Sales Manager", "Stock Manager"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)

    def generate_verification_code(self):
        # Generate a 6-digit random verification code
        return get_random_string(length=6, allowed_chars='1234567890')

    
class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)  # Associate product with a store
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    size_range = models.ForeignKey(SizeRange, on_delete=models.CASCADE)
    colors = models.ManyToManyField(Color)
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    initial_quantity = models.PositiveIntegerField()
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_stock_threshold = models.PositiveIntegerField(default=1, blank=True)
    supplier = models.CharField(max_length=100, null=True, blank=True)
    image_url = models.URLField(blank=True, null=True)
    created_by = models.CharField(max_length=100, default="admin")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.code} - {self.brand} - {self.size_range}"

    def total_quantity_sold(self):
        return self.sales_transactions.aggregate(total=Sum('quantity_sold')).get('total') or 0

class Stock(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)  # Associate stock with a store
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='stock', unique=True)
    stock_on_hand = models.PositiveIntegerField("Quantity", default=0, blank=True)
    low_stock_threshold = models.PositiveIntegerField(default=1, blank=True)
    created_by = models.CharField(max_length=100, default="admin")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product} - Stock on Hand: {self.stock_on_hand}"

    def update_stock_on_hand(self, quantity):
        """
        Update the stock on hand for the product associated with this stock.
        """
        self.stock_on_hand += quantity
        self.save()

class StockTransaction(models.Model):
    STOCK_TYPES = (('1', 'In 🟢'), ('2', 'Out🔺'))
    store = models.ForeignKey(Store, on_delete=models.CASCADE)  # Associate stock transaction with a store
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_transactions')
    quantity = models.IntegerField()
    stock_type = models.CharField(max_length=1, choices=STOCK_TYPES)
    modified_by = models.CharField(max_length=100)
    stock_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product} - {self.quantity} - {self.get_stock_type_display()}"


class SalesTransaction(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)  # Associate sales transaction with a store
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sales_transactions')
    quantity_sold = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    sold_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product} - {self.quantity_sold} - {self.total_amount}"
    
    # the default value for selling_price should be the selling price of the product
    def save(self, *args, **kwargs):
        if self.unit_price is None:
            self.unit_price = self.product.selling_price
        self.total_amount = self.quantity_sold * self.unit_price
        super().save(*args, **kwargs)
