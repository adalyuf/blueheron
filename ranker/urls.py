from django.urls import path
from ranker import views

urlpatterns = [
    path("", views.domain_list, name="home"),
    path("domains/", views.domain_list, name="domain_list"),
    path('domains/<int:domain_id>/', views.domain_detail, name='domain_detail'),

    path('keywordfile_make_primary/<int:domain_id>/<int:keywordfile_id>', views.keywordfile_make_primary, name='keywordfile_make_primary'),

    path('conversations/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('conversations/add/<int:product_id>/<int:domain_id>/', views.conversation_add, name='conversation_add'),
    path('conversations/edit/<int:conversation_id>/', views.conversation_edit, name='conversation_edit'),
    path('conversations/edit/<int:conversation_id>/update_order/', views.conversation_update_order, name='conversation_update_order'),
    path('conversations/edit/<int:conversation_id>/get_responses/', views.conversation_get_responses, name='conversation_get_responses'),


    path('messages/delete/<int:message_id>/', views.message_delete, name='message_delete'),


    path("products/", views.product_list, name="product_list"),
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),
    path("products/<int:product_id>/update_order/", views.product_template_order, name="product_template_order"),
    path("product_templates/delete/<int:producttemplate_id>", views.product_template_delete, name="product_template_delete"),

]