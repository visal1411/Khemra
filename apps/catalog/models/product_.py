from django.db import models


class Product(models.Model):
    name = models.CharField(
        max_length=255,
        help_text="Name of the product"
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed description of the product"
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Current selling price of the product"
    )

    stock_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Current available stock quantity"
    )

    image_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL of the product image"
    )

    is_available = models.BooleanField(
        default=True,
        help_text="Indicates whether the product is currently available"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name