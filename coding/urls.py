from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from coding import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('coding.api_urls')),
    path('', views.index, name='home'),
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico')),  # fixes 404 favicon
]
