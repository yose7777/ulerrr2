from django.urls import path
from . import views

urlpatterns = [

    path('video/<int:cam_id>', views.video_feed),

    path('data', views.get_data),

    path('set_threshold', views.set_threshold),

    path('set_classification', views.set_classification),

]