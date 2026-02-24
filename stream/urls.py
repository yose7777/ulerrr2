from django.urls import path
from . import views

urlpatterns = [
    path('video_feed/', views.video_feed),
    path('data_feed/', views.data_feed),
    path('set_threshold/', views.set_threshold),
    path('set_classification/', views.set_classification),
]