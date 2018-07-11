from django.urls import path

from . import views

app_name = 'app'
urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add, name='add'),
    path('edit/', views.edit, name='edit'),
    path('delete/', views.delete, name='delete'),
    path('archive_toggle/', views.archive_toggle, name='archive_toggle'),
    path('search/', views.search, name='search'),
    path('archived/', views.archived, name='archived'),
    path('student/', views.student, name='student'),
    path('clear/', views.clear, name='clear'),
]
