from django.db import models 

class Brand(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class SizeRange(models.Model):
    name = models.CharField(max_length=100)
    size_value = models.CharField(max_length=6)
    
    def __str__(self):
        return f"{self.name} - {self.size_value}"

class Color(models.Model):
    name = models.CharField(max_length=100)
    color_code = models.CharField(max_length=10)
    def __str__(self):
        return self.name
    
class Product(models.Model):
    COLOR_CHOICES = [
        ('red', 'Red'),
        ('blue', 'Blue'),
        ('green', 'Green'),
        ('yellow', 'Yellow'),
        ('black', 'Black'),
        ('white', 'White'),
        ('purple', 'Purple'),
        ('orange', 'Orange'),
        ('brown', 'Brown'),
        ('grey', 'Grey'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('pink', 'Pink'),
        ('beige', 'Beige'),
        ('cream', 'Cream'),
        ('multi', 'Multi'),
    ]
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, default=1)
    size_range = models.ForeignKey(SizeRange, on_delete=models.CASCADE)
    colors = models.ManyToManyField(Color)
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    initial_quantity = models.PositiveIntegerField()
    quantity_available = models.PositiveIntegerField(default=0, null=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    image_url = models.URLField(blank=True, null=True)
    created_by = models.CharField(max_length=100, default="admin")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.code} - {self.brand} - {self.size_range}"
    
    # # set the quantity available to the quantity of the product if the product is created for the first time
    def save(self, *args, **kwargs):
        if not self.pk:
            self.quantity_available = self.quantity
        super(Product, self).save(*args, **kwargs)


class SalesTransaction(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_sold = models.PositiveIntegerField()
    sale_date = models.DateField(auto_now_add=True)
    soled_by = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.product} - {self.quantity_sold} units - {self.sale_date}"
        
class StockTransaction(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_added = models.PositiveIntegerField()
    size_range = models.ForeignKey(SizeRange, on_delete=models.CASCADE)
    stock_date = models.DateField(auto_now_add=True)
    added_by = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.product} - {self.quantity_added} units - {self.stock_date}"
    

        