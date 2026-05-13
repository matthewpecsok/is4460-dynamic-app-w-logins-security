import json
from collections import Counter, deque
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView, View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect

from .forms import OrderForm, CustomerRegistrationForm
from .models import Order, Product


class IsEmployeeMixin(UserPassesTestMixin):
	"""Mixin to check if user is in employee group"""
	def test_func(self):
		return self.request.user.groups.filter(name="employee").exists()


class IsCustomerMixin(UserPassesTestMixin):
	"""Mixin to check if user is in customer group"""
	def test_func(self):
		return self.request.user.groups.filter(name="customer").exists()


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


class ProductCreateView(IsEmployeeMixin, CreateView):
	model = Product
	fields = ["name", "description", "price", "in_stock"]


class ProductUpdateView(IsEmployeeMixin, UpdateView):
	model = Product
	fields = ["name", "description", "price", "in_stock"]


class ProductDeleteView(IsEmployeeMixin, DeleteView):
	model = Product
	success_url = reverse_lazy("product_list")


class OrderListView(IsEmployeeMixin, ListView):
	model = Order
	context_object_name = "orders"


class OrderDetailView(IsEmployeeMixin, DetailView):
	model = Order


class OrderCreateView(LoginRequiredMixin, CreateView):
	model = Order
	form_class = OrderForm
	login_url = "login"
	
	def form_valid(self, form):
		form.instance.customer = self.request.user
		return super().form_valid(form)


class OrderUpdateView(IsEmployeeMixin, UpdateView):
	model = Order
	form_class = OrderForm


class OrderDeleteView(IsEmployeeMixin, DeleteView):
	model = Order
	success_url = reverse_lazy("order_list")


class DashboardView(IsEmployeeMixin, TemplateView):
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


class CustomerRegistrationView(CreateView):
	form_class = CustomerRegistrationForm
	template_name = "shop/register.html"
	success_url = reverse_lazy("login")


class LoginView(TemplateView):
	template_name = "shop/login.html"

	def post(self, request, *args, **kwargs):
		username = request.POST.get("username")
		password = request.POST.get("password")
		user = authenticate(request, username=username, password=password)
		
		if user is not None:
			login(request, user)
			# Redirect based on group membership
			if user.groups.filter(name="employee").exists():
				return redirect("dashboard")
			else:
				return redirect("product_list")
		else:
			context = self.get_context_data()
			context["error"] = "Invalid username or password"
			return self.render_to_response(context)


class LogoutView(View):
	def get(self, request, *args, **kwargs):
		logout(request)
		return redirect("login")
