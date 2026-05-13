import pytest
from django.urls import reverse

from .models import Order, Product


@pytest.mark.django_db
def test_homepage_loads(client):
	response = client.get(reverse("home"))

	assert response.status_code == 200
	assert "shop/home.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_dashboard_loads(client):
	response = client.get(reverse("dashboard"))

	assert response.status_code == 200
	assert "shop/dashboard.html" in [t.name for t in response.templates]
	assert b"Internal Monitoring Dashboard" in response.content


@pytest.fixture
def product(db):
	return Product.objects.create(
		name="Rose Bouquet",
		description="A dozen red roses.",
		price="39.99",
		in_stock=True,
	)


@pytest.mark.django_db
def test_create_product(client):
	response = client.post(
		reverse("product_create"),
		{
			"name": "Sunflower Bundle",
			"description": "Bright yellow sunflowers.",
			"price": "24.50",
			"in_stock": True,
		},
	)

	assert response.status_code == 302
	assert Product.objects.count() == 1
	created_product = Product.objects.get(name="Sunflower Bundle")
	assert response["Location"] == reverse("product_detail", kwargs={"pk": created_product.pk})


@pytest.mark.django_db
def test_list_products(client, product):
	response = client.get(reverse("product_list"))

	assert response.status_code == 200
	assert b"Rose Bouquet" in response.content


@pytest.mark.django_db
def test_retrieve_product_detail(client, product):
	response = client.get(reverse("product_detail", kwargs={"pk": product.pk}))

	assert response.status_code == 200
	assert b"A dozen red roses." in response.content


@pytest.mark.django_db
def test_update_product(client, product):
	response = client.post(
		reverse("product_update", kwargs={"pk": product.pk}),
		{
			"name": "Rose Bouquet Deluxe",
			"description": "Two dozen red roses.",
			"price": "59.99",
			"in_stock": False,
		},
	)

	assert response.status_code == 302
	product.refresh_from_db()
	assert product.name == "Rose Bouquet Deluxe"
	assert str(product.price) == "59.99"
	assert product.in_stock is False


@pytest.mark.django_db
def test_delete_product(client, product):
	response = client.post(reverse("product_delete", kwargs={"pk": product.pk}))

	assert response.status_code == 302
	assert response["Location"] == reverse("product_list")
	assert not Product.objects.filter(pk=product.pk).exists()


@pytest.fixture
def products(db):
	product_one = Product.objects.create(
		name="Tulip Bunch",
		description="Mixed color tulips.",
		price="19.99",
		in_stock=True,
	)
	product_two = Product.objects.create(
		name="Lily Arrangement",
		description="White lilies in a glass vase.",
		price="29.99",
		in_stock=True,
	)
	return product_one, product_two


@pytest.fixture
def order(products):
	product_one, _ = products
	o = Order.objects.create(customer_name="Alice")
	o.products.add(product_one)
	return o


@pytest.mark.django_db
def test_create_order_with_multiple_products(client, products):
	product_one, product_two = products
	response = client.post(
		reverse("order_create"),
		{
			"customer_name": "Bob",
			"products": [product_one.pk, product_two.pk],
		},
	)

	assert response.status_code == 302
	assert Order.objects.count() == 1
	created_order = Order.objects.get(customer_name="Bob")
	assert created_order.products.count() == 2
	assert response["Location"] == reverse("order_detail", kwargs={"pk": created_order.pk})


@pytest.mark.django_db
def test_list_orders(client, order):
	response = client.get(reverse("order_list"))

	assert response.status_code == 200
	assert b"Alice" in response.content


@pytest.mark.django_db
def test_retrieve_order_detail(client, order):
	response = client.get(reverse("order_detail", kwargs={"pk": order.pk}))

	assert response.status_code == 200
	assert b"Tulip Bunch" in response.content


@pytest.mark.django_db
def test_update_order_products(client, order, products):
	_, product_two = products
	response = client.post(
		reverse("order_update", kwargs={"pk": order.pk}),
		{
			"customer_name": "Alice Cooper",
			"products": [product_two.pk],
		},
	)

	assert response.status_code == 302
	order.refresh_from_db()
	assert order.customer_name == "Alice Cooper"
	assert list(order.products.values_list("pk", flat=True)) == [product_two.pk]


@pytest.mark.django_db
def test_delete_order(client, order):
	response = client.post(reverse("order_delete", kwargs={"pk": order.pk}))

	assert response.status_code == 302
	assert response["Location"] == reverse("order_list")
	assert not Order.objects.filter(pk=order.pk).exists()

