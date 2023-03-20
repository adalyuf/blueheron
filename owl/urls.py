from django.urls import path
from owl import views

urlpatterns = [
    path("", views.domain_list, name="home"),
    path("domains", views.domain_list, name="domain_list"),
    path('domains/<int:domain_id>/', views.domain_detail, name='domain_detail'),
    path('keywordfile_make_primary/<int:domain_id>/<int:keywordfile_id>', views.keywordfile_make_primary, name='keywordfile_make_primary'),
    path('conversations/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
]