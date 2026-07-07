from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from .models import Product, Category, Review
from .forms import ProductForm, ReviewForm


def is_seller(user):
    return user.is_authenticated and user.is_seller


# Rotating hero banner slides — Amazon-style category carousel.
# Each slide uses a CSS gradient "scene" (css_class) instead of a hotlinked photo,
# so the banner never breaks and needs no external image hosting.
#
# TO SWAP IN REAL PHOTOGRAPHY LATER:
#   1. Drop your image files into static/images/hero/ (e.g. electronics.jpg)
#   2. In static/css/style.css, find the matching ".hero-slide--<name>" rule
#      and add:  background-image: url('/static/images/hero/electronics.jpg');
#      background-size: cover; background-position: center;
#   3. That's it — the gradient becomes a photo, everything else (timing,
#      dots, fade transition) keeps working unchanged.
HERO_SLIDES = [
    {
        'name': 'electronics',
        'eyebrow': 'Tech Deals',
        'title': 'Level Up Your Setup',
        'subtitle': 'Save big on headphones, TVs, and smart home gear.',
        'cta_text': 'Shop Electronics',
        'category_slug': 'electronics',
        'css_class': 'hero-slide--electronics',
    },
    {
        'name': 'fashion',
        'eyebrow': 'New Season',
        'title': 'Refresh Your Wardrobe',
        'subtitle': 'Denim, footwear, and everyday essentials on sale.',
        'cta_text': 'Shop Fashion',
        'category_slug': 'fashion',
        'css_class': 'hero-slide--fashion',
    },
    {
        'name': 'home',
        'eyebrow': 'Home Refresh',
        'title': 'Upgrade Every Room',
        'subtitle': 'Cookware, robot vacuums, and more for your home.',
        'cta_text': 'Shop Home & Kitchen',
        'category_slug': 'home-kitchen',
        'css_class': 'hero-slide--home',
    },
    {
        'name': 'sports',
        'eyebrow': 'Get Moving',
        'title': 'Gear Up for Fitness',
        'subtitle': 'Yoga mats, dumbbells, and outdoor essentials.',
        'cta_text': 'Shop Sports & Outdoors',
        'category_slug': 'sports-outdoors',
        'css_class': 'hero-slide--sports',
    },
    {
        'name': 'books',
        'eyebrow': "Reader's Corner",
        'title': 'Your Next Favorite Read',
        'subtitle': 'Fiction, guides, and everything in between.',
        'cta_text': 'Shop Books',
        'category_slug': 'books',
        'css_class': 'hero-slide--books',
    },
]


def home(request):
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '')

    products = Product.objects.filter(is_active=True)

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    if category_slug:
        products = products.filter(category__slug=category_slug)

    categories = Category.objects.all()
    featured_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'featured_products': featured_products,
        'query': query,
        'selected_category': category_slug,
        'hero_slides': HERO_SLIDES,
    }
    return render(request, 'products/home.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    reviews = product.reviews.all()
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk)[:4]

    review_form = None
    if request.user.is_authenticated:
        if request.method == 'POST':
            review_form = ReviewForm(request.POST)
            if review_form.is_valid():
                review, created = Review.objects.update_or_create(
                    product=product, user=request.user,
                    defaults={
                        'rating': review_form.cleaned_data['rating'],
                        'comment': review_form.cleaned_data['comment'],
                    }
                )
                messages.success(request, "Thanks for your review!")
                return redirect('products:product_detail', slug=slug)
        else:
            review_form = ReviewForm()

    context = {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
        'review_form': review_form,
    }
    return render(request, 'products/product_detail.html', context)


@login_required
@user_passes_test(is_seller, login_url='accounts:login')
def seller_dashboard(request):
    products = Product.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'products/seller_dashboard.html', {'products': products})


@login_required
@user_passes_test(is_seller, login_url='accounts:login')
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            messages.success(request, f'"{product.name}" was listed successfully.')
            return redirect('products:seller_dashboard')
    else:
        form = ProductForm()
    return render(request, 'products/product_form.html', {'form': form, 'action': 'Add'})


@login_required
@user_passes_test(is_seller, login_url='accounts:login')
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{product.name}" was updated.')
            return redirect('products:seller_dashboard')
    else:
        form = ProductForm(instance=product)
    return render(request, 'products/product_form.html', {'form': form, 'action': 'Edit'})


@login_required
@user_passes_test(is_seller, login_url='accounts:login')
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'"{name}" was deleted.')
        return redirect('products:seller_dashboard')
    return render(request, 'products/product_confirm_delete.html', {'product': product})
