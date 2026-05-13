from django.contrib import admin

from .models import Order, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ("name", "price", "in_stock", "created_at")
	search_fields = ("name",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ("id", "customer_name", "created_at")
	search_fields = ("customer_name",)
	filter_horizontal = ("products",)

# Register your models here.
