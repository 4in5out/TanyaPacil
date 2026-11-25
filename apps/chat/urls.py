from django.urls import path

from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/chat/send/', views.send_message_api, name='send_api'),
    path('api/chat/history/', views.history_api, name='history_api'),
    path('api/chat/reset/', views.reset_session_api, name='reset_api'),
]
