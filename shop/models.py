from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class Product(models.Model):
	name = models.CharField(max_length=120)
	description = models.TextField(blank=True)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	in_stock = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.name

	def get_absolute_url(self):
		return reverse("product_detail", kwargs={"pk": self.pk})


class Order(models.Model):
	customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders", null=True, blank=True)
	customer_name = models.CharField(max_length=120)
	products = models.ManyToManyField(Product, related_name="orders", blank=False)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Order #{self.pk} for {self.customer_name}"

	def get_absolute_url(self):
		return reverse("order_detail", kwargs={"pk": self.pk})
