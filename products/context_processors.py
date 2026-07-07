from .models import Category


def all_categories(request):
    """Makes the category list available in every template (for the mobile sidebar)."""
    return {'all_categories': Category.objects.all()}
