from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from coding.views import index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('coding.api_urls')),
    path('', index, name='home'),
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico')),  # ✅ handles browser requests
]
