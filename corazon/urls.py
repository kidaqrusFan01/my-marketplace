from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('products.urls')),
    path('accounts/', include('accounts.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('jobs/', include('jobs.urls')),
]

admin.site.site_header = "Corazon Marketplace Admin"
admin.site.site_title = "Corazon Marketplace"
admin.site.index_title = "Manage your store"

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Media (user-uploaded product images, resumes) is served directly by Django
# regardless of DEBUG. Note: Django's static() helper silently does nothing
# when DEBUG=False, so we wire the view up manually here instead — that's
# what actually makes uploads work outside of `runserver`+DEBUG=True.
# This is fine for a small/medium site like this one. If you outgrow it,
# switch to a real file host (S3, Cloudinary, etc.) — see README.md
# "Going to Production".
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),
]
