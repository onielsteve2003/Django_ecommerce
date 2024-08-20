from django.contrib.auth import get_user_model
from django.db import models
from django.apps import apps

User = get_user_model()

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField()
    category = models.ForeignKey(
        'store.Category',
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='products/')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')

    def __str__(self):
        return self.name
