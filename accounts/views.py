from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy

from .forms import CustomerSignUpForm, SellerSignUpForm, ProfileUpdateForm
from orders.models import Order


class CustomerSignUpView(CreateView):
    form_class = CustomerSignUpForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('products:home')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['user_type'] = 'customer'
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Welcome to Corazon Marketplace! Your account was created.")
        return response


class SellerSignUpView(CreateView):
    form_class = SellerSignUpForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('products:seller_dashboard')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['user_type'] = 'seller'
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Welcome, seller! You can now list products from your dashboard.")
        return response


class CorazonLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


class CorazonLogoutView(LogoutView):
    next_page = 'products:home'


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    orders = Order.objects.filter(customer=request.user).order_by('-created_at')[:10]
    return render(request, 'accounts/profile.html', {'form': form, 'orders': orders})
