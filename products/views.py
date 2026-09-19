from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .models import Product, Category, Review, HeroBanner, DealOfTheDay
from .forms import ProductForm, ReviewForm


def is_seller(user):
    return user.is_authenticated and user.is_seller


def seller_required(view_func):
    """
    Guards seller-only views. This is deliberately NOT
    @login_required + @user_passes_test(is_seller, login_url='accounts:login'):
    that combination sends an authenticated-but-not-a-seller user to the
    login page, and CorazonLoginView's redirect_authenticated_user=True
    immediately bounces an already-logged-in user straight back to
    `next` — which fails the seller test again, straight back to login,
    forever. An anonymous visitor still goes to login as normal; a logged
    -in customer instead gets a clear message and a way to become a seller.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('accounts:login')}?next={request.path}")
        if not request.user.is_seller:
            messages.info(request, "You need a seller account to access that page.")
            return redirect('accounts:signup_seller')
        return view_func(request, *args, **kwargs)
    return wrapper


def build_referral_share_url(request, path):
    """
    Absolute URL for `path`, tagged with the current user's referral code
    (?ref=CODE) so anyone who clicks a shared link and later buys something
    can be credited back to them — see accounts.middleware and
    loyalty.views.track_share. Anonymous visitors get a plain link with no
    ref tag (nothing to attribute the share to).
    """
    url = request.build_absolute_uri(path)
    if request.user.is_authenticated:
        separator = '&' if '?' in url else '?'
        url = f"{url}{separator}ref={request.user.referral_code}"
    return url


# Fallback content used ONLY if no HeroBanner rows exist yet (e.g. right
# after a fresh migrate, before anyone has added banners in admin) — so the
# homepage never looks broken/empty on a brand-new install.
DEFAULT_HERO_SLIDES = [
    {'eyebrow': 'Tech Deals', 'title': 'Level Up Your Setup',
     'subtitle': 'Save big on headphones, TVs, and smart home gear.',
     'cta_text': 'Shop Electronics', 'category_slug': 'electronics', 'placeholder_style': 'electronics'},
    {'eyebrow': 'New Season', 'title': 'Refresh Your Wardrobe',
     'subtitle': 'Denim, footwear, and everyday essentials on sale.',
     'cta_text': 'Shop Fashion', 'category_slug': 'fashion', 'placeholder_style': 'fashion'},
    {'eyebrow': 'Home Refresh', 'title': 'Upgrade Every Room',
     'subtitle': 'Cookware, robot vacuums, and more for your home.',
     'cta_text': 'Shop Home & Kitchen', 'category_slug': 'home-kitchen', 'placeholder_style': 'home'},
    {'eyebrow': 'Get Moving', 'title': 'Gear Up for Fitness',
     'subtitle': 'Yoga mats, dumbbells, and outdoor essentials.',
     'cta_text': 'Shop Sports & Outdoors', 'category_slug': 'sports-outdoors', 'placeholder_style': 'sports'},
    {'eyebrow': "Reader's Corner", 'title': 'Your Next Favorite Read',
     'subtitle': 'Fiction, guides, and everything in between.',
     'cta_text': 'Shop Books', 'category_slug': 'books', 'placeholder_style': 'books'},
]


def get_hero_slides():
    """
    Builds the list of slides for the homepage carousel from HeroBanner rows
    in the database (managed via Django admin -> Hero Banners). Each slide
    gets either a real uploaded photo (image_url) or falls back to a
    gradient + icon placeholder (placeholder_style) if no image was
    uploaded for that banner yet.
    """
    banners = HeroBanner.objects.filter(is_active=True).select_related('category')

    if not banners.exists():
        # Nothing configured yet in admin — show sensible defaults instead
        # of an empty carousel.
        return [
            {**slide, 'image_url': None, 'css_class': f"hero-slide--{slide['placeholder_style']}"}
            for slide in DEFAULT_HERO_SLIDES
        ]

    slides = []
    for banner in banners:
        slides.append({
            'eyebrow': banner.eyebrow,
            'title': banner.title,
            'subtitle': banner.subtitle,
            'cta_text': banner.cta_text,
            'category_slug': banner.category.slug if banner.category else '',
            'placeholder_style': banner.placeholder_style,
            'css_class': f"hero-slide--{banner.placeholder_style}",
            'image_url': banner.image.url if banner.image else None,
        })
    return slides


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

    current_deal = DealOfTheDay.get_current()

    from marketing.models import Advertisement
    advertisements = Advertisement.objects.filter(is_active=True)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'featured_products': featured_products,
        'query': query,
        'selected_category': category_slug,
        'current_deal': current_deal,
        'deal_share_url': build_referral_share_url(request, current_deal.product.get_absolute_url()) if current_deal else None,
        'hero_slides': get_hero_slides(),
        'advertisements': advertisements,
    }
    return render(request, 'products/home.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    reviews = product.reviews.all()
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk)[:4]

    from loyalty.services import product_is_current_deal
    is_deal_of_day = product_is_current_deal(product)

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
        'share_url': build_referral_share_url(request, product.get_absolute_url()),
        'is_deal_of_day': is_deal_of_day,
    }
    return render(request, 'products/product_detail.html', context)


@seller_required
def seller_dashboard(request):
    products = Product.objects.filter(seller=request.user).order_by('-created_at')

    # Precompute each product's referral-tagged share link here rather than
    # in the template, since it needs the request object.
    products_with_share = [
        {'product': p, 'share_url': build_referral_share_url(request, p.get_absolute_url())}
        for p in products
    ]

    from marketing.models import VendorSubscription
    subscription = VendorSubscription.objects.filter(seller=request.user).first()
    current_plan = subscription.current_plan if subscription else 'free'

    return render(request, 'products/seller_dashboard.html', {
        'products_with_share': products_with_share,
        'current_plan': current_plan,
    })


@seller_required
def vendor_page(request):
    """
    A vendor's own profile/analytics page: who they are, what they sell,
    and how their product-sharing is performing — both their own sharing
    activity (which earns them Loyalty Coin, see loyalty.views.track_share)
    and, separately, how often anyone (including customers) has shared
    their products, as a rough reach/popularity signal.
    """
    vendor = request.user
    products = Product.objects.filter(seller=vendor)

    from django.db.models import Sum, Count
    from marketing.models import VendorSubscription
    from loyalty.models import LoyaltyAccount, LoyaltyTransaction

    account = LoyaltyAccount.get_or_create_for(vendor)

    # Shares the vendor personally performed (from their dashboard's Share
    # buttons) — this is what actually earns THEM Loyalty Coin.
    own_shares = LoyaltyTransaction.objects.filter(
        account=account, reason='share'
    ).select_related('related_product')

    total_shares_by_vendor = own_shares.count()
    total_bonus_from_shares = own_shares.aggregate(total=Sum('points'))['total'] or 0

    # Per-product breakdown of the vendor's own shares.
    shared_products = {}
    for txn in own_shares:
        if not txn.related_product:
            continue
        entry = shared_products.setdefault(txn.related_product.id, {
            'product': txn.related_product, 'share_count': 0, 'points_earned': 0,
        })
        entry['share_count'] += 1
        entry['points_earned'] += txn.points
    shared_products = sorted(shared_products.values(), key=lambda e: -e['share_count'])

    # Broader signal: how many times ANYONE has shared each of this
    # vendor's products (customers sharing a product earn points
    # themselves, not the vendor — this is just reach, not the vendor's
    # own bonus).
    product_reach = (
        LoyaltyTransaction.objects.filter(reason='share', related_product__seller=vendor)
        .values('related_product', 'related_product__name', 'related_product__slug')
        .annotate(total_shares=Count('id'))
        .order_by('-total_shares')
    )
    total_reach_shares = sum(row['total_shares'] for row in product_reach)

    subscription = VendorSubscription.objects.filter(seller=vendor).first()
    current_plan = subscription.current_plan if subscription else 'free'

    return render(request, 'products/vendor_page.html', {
        'vendor': vendor,
        'products_count': products.count(),
        'active_products_count': products.filter(is_active=True).count(),
        'current_plan': current_plan,
        'loyalty_balance': account.balance,
        'total_shares_by_vendor': total_shares_by_vendor,
        'total_bonus_from_shares': total_bonus_from_shares,
        'shared_products': shared_products,
        'product_reach': product_reach,
        'total_reach_shares': total_reach_shares,
    })


@seller_required
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


@seller_required
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


@seller_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'"{name}" was deleted.')
        return redirect('products:seller_dashboard')
    return render(request, 'products/product_confirm_delete.html', {'product': product})
