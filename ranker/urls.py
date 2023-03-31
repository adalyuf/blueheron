from django.urls import path
from ranker import views

urlpatterns = [
    path("", views.DomainListView.as_view(), name="home"),

    path('dashboard/', views.DashboardsView.as_view(template_name = 'pages/dashboards/index.html'), name='dashboard'),

    path("domains/", views.DomainListView.as_view(), name="domain_list"),
    path('domains/<int:domain_id>/', views.domain_detail, name='domain_detail'),

    path('keywordfile_make_primary/<int:domain_id>/<int:keywordfile_id>', views.keywordfile_make_primary, name='keywordfile_make_primary'),

    path('conversations/<int:conversation_id>/'                     , views.conversation_detail                 , name='conversation_detail'),
    path('conversations/add/<int:template_id>/<int:domain_id>/'     , views.conversation_add                    , name='conversation_add'),
    path('conversations/edit/<int:conversation_id>/'                , views.conversation_edit                   , name='conversation_edit'),
    path('conversations/edit/<int:conversation_id>/update_order/'   , views.conversation_update_order           , name='conversation_update_order'),
    path('conversations/edit/<int:conversation_id>/get_responses/'  , views.conversation_get_responses          , name='conversation_get_responses'),

    path('messages/delete/<int:message_id>/', views.message_delete, name='message_delete'),

    path("templates/"                                   , views.GetTemplateListView.as_view()   , name="template_list"),
    path("templates/<int:pk>/"                          , views.GetTemplateView.as_view()       , name="template_detail"),
    path("templates/<int:template_id>/update_order/"    , views.template_item_order             , name="template_item_order"),
    path("template_items/delete/<int:TemplateItem_id>"  , views.template_item_delete            , name="template_item_delete"),

]