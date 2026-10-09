from django.urls import path
from . import views

urlpatterns = [
    path('', views.yard_view, name='yard'),
    path('register/', views.register_view, name='register'),
    path('feed/', views.feed_view, name='feed'),
    path('accelerate-feed/', views.accelerate_feed_view, name='accelerate_feed'),
    path('collect/<int:egg_id>/', views.collect_egg_view, name='collect_egg'),
    path('community/', views.community_view, name='community'),
    path('profile/', views.profile_view, name='profile'),
    path('stats/', views.stats_view, name='stats'),
    path('chat/', views.chat_view, name='chat'),
    path('like/<int:photo_id>/', views.like_view, name='like'),
    path('comment/<int:photo_id>/', views.comment_view, name='comment'),
    path('pin/<int:photo_id>/', views.pin_photo_view, name='pin'),
    path('delete-photo/<int:photo_id>/', views.delete_photo_view, name='delete_photo'),
]
