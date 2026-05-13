import json
from collections import Counter, deque
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import OrderForm
from .models import Order, Product


class HomePageView(TemplateView):
	template_name = "shop/home.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["products"] = Product.objects.order_by("name")
		context["orders"] = Order.objects.order_by("-created_at")[:5]
		return context


class ProductListView(ListView):
	model = Product
	context_object_name = "products"


class ProductDetailView(DetailView):
	model = Product


class ProductCreateView(CreateView):
	model = Product
	fields = ["name", "description", "price", "in_stock"]


class ProductUpdateView(UpdateView):
	model = Product
	fields = ["name", "description", "price", "in_stock"]


class ProductDeleteView(DeleteView):
	model = Product
	success_url = reverse_lazy("product_list")


class OrderListView(ListView):
	model = Order
	context_object_name = "orders"


class OrderDetailView(DetailView):
	model = Order


class OrderCreateView(CreateView):
	model = Order
	form_class = OrderForm


class OrderUpdateView(UpdateView):
	model = Order
	form_class = OrderForm


class OrderDeleteView(DeleteView):
	model = Order
	success_url = reverse_lazy("order_list")


class DashboardView(TemplateView):
	template_name = "shop/dashboard.html"
	log_limit = 50

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		recent_logs = self._read_recent_logs()
		level_counts = Counter(log.get("level", "INFO") for log in recent_logs)
		since = timezone.now() - timedelta(hours=24)

		context["metrics"] = {
			"product_count": Product.objects.count(),
			"out_of_stock_count": Product.objects.filter(in_stock=False).count(),
			"order_count": Order.objects.count(),
			"orders_last_24h": Order.objects.filter(created_at__gte=since).count(),
		}
		context["log_counts"] = {
			"INFO": level_counts.get("INFO", 0),
			"WARNING": level_counts.get("WARNING", 0),
			"ERROR": level_counts.get("ERROR", 0),
		}
		context["recent_logs"] = recent_logs
		return context

	def _read_recent_logs(self):
		log_path = Path(settings.LOG_FILE_PATH)
		if not log_path.exists():
			return []

		lines = deque(maxlen=self.log_limit)
		with log_path.open("r", encoding="utf-8") as log_file:
			for line in log_file:
				lines.append(line.strip())

		entries = []
		for line in reversed(lines):
			if not line:
				continue
			try:
				parsed = json.loads(line)
			except json.JSONDecodeError:
				continue

			payload = parsed.get("payload", {})
			entries.append(
				{
					"timestamp": parsed.get("timestamp", ""),
					"level": parsed.get("level", ""),
					"message": parsed.get("message", ""),
					"method": payload.get("method", ""),
					"path": payload.get("path", ""),
					"status_code": payload.get("status_code", ""),
					"duration_ms": payload.get("duration_ms", ""),
				}
			)

		return entries
