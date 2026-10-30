from django.urls import path
from . import views

app_name = 'password_reset'

urlpatterns = [
    path('submit/', views.submit_password_reset_request, name='submit_request'),
    path('list/', views.list_password_reset_requests, name='list_requests'),
    path('<int:request_id>/detail/', views.get_password_reset_request_detail, name='request_detail'),
    path('<int:request_id>/approve/', views.approve_password_reset_request, name='approve_request'),
    path('<int:request_id>/reject/', views.reject_password_reset_request, name='reject_request'),
] 