from django.urls import path
from .views import predict_cpt_from_image, predict_cpt_from_text

urlpatterns = [
    path('predict/image/', predict_cpt_from_image, name='predict_cpt_image'),
    path('predict/text/', predict_cpt_from_text, name='predict_cpt_text'),
    path('predict/', predict_cpt_from_text, name='predict_cpt_fallback'),  # ✅ changed this
]
