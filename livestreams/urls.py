from django.urls import path

from . import views

urlpatterns = [
    path('go-live/', views.go_live, name='go-live'),
    path('livestreams/<int:pk>/', views.livestream_page, name='livestream-page'),
    path('api/livestreams/', views.api_active_streams, name='api-active-streams'),
    path('api/livestreams/<int:pk>/status/', views.api_stream_status, name='api-stream-status'),
    path('livestreams/callback/on_publish/', views.srs_on_publish, name='srs-on-publish'),
    path('livestreams/callback/on_unpublish/', views.srs_on_unpublish, name='srs-on-unpublish'),
]
