import os
import django
import json
from django.core import serializers

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "badris_foods.settings")
django.setup()

from products.models import Category, Product

data = serializers.serialize(
    "json",
    list(Category.objects.all()) + list(Product.objects.all()),
    indent=2
)

with open("products_data.json", "w", encoding="utf-8") as f:
    f.write(data)

print("products_data.json created successfully")