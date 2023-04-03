from django.urls import path
from ranker import views
from ranker.domains import views as domain_views
from ranker.conversations import views as conv_views
from ranker.projects import views as project_views

urlpatterns = [
    path("", domain_views.DomainListView.as_view(), name="home"),

    path('dashboard/', views.DashboardsView.as_view(template_name = 'pages/dashboards/index.html'), name='dashboard'),

    path("domains/"                                 , domain_views.DomainListView.as_view()     , name="domain_list"),
    path("domain_search/"                           , domain_views.domain_search                , name="domain_search"),
    path('domains/<int:domain_id>/'                 , domain_views.domain_detail                , name='domain_detail'),

    path('keywordfile_make_primary/<int:domain_id>/<int:keywordfile_id>/', domain_views.keywordfile_make_primary, name='keywordfile_make_primary'),

    path('conversations/<int:conversation_id>/'                     , conv_views.conversation_detail                 , name='conversation_detail'),
    path('conversations/add/<int:template_id>/<int:domain_id>/<int:ai_model_id>/', conv_views.conversation_add       , name='conversation_add'),
    path('conversations/edit/<int:conversation_id>/'                , conv_views.conversation_edit                   , name='conversation_edit'),
    path('conversations/edit/<int:conversation_id>/update_order/'   , conv_views.conversation_update_order           , name='conversation_update_order'),
    path('conversations/edit/<int:conversation_id>/get_responses/'  , conv_views.conversation_get_responses          , name='conversation_get_responses'),

    path('messages/delete/<int:message_id>/'            , conv_views.message_delete, name='message_delete'),

    path("templates/"                                   , views.TemplateListView.as_view()   , name="template_list"),
    path("templates/create/"                            , views.template_create                 , name="template_create"),
    path("templates/create/<int:project_id>/"           , views.template_create                 , name="template_create"),
    path("templates/<int:pk>/"                          , views.GetTemplateView.as_view()       , name="template_detail"),
    path("templates/delete/<int:template_id>/"          , views.template_delete                 , name="template_delete"),
    path("templates/<int:template_id>/update_order/"    , views.template_item_order             , name="template_item_order"),
    path("template_items/delete/<int:TemplateItem_id>/" , views.template_item_delete            , name="template_item_delete"),

    path("projects/"                                    , project_views.ProjectListView.as_view()       , name="project_list"),
    path("projects/<int:project_id>/"                   , project_views.project_detail                  , name="project_detail"),
    path("projects/<int:project_id>/add_domain/"        , project_views.project_add_domain              , name="project_add_domain"),
    path("projects/<int:project_id>/remove_domain/"     , project_views.project_remove_domain           , name="project_remove_domain"),
    path('projects/create/'                             , project_views.ProjectCreate.as_view()         , name='project_create'),
    path('projects/<int:pk>/update/'                    , project_views.ProjectUpdate.as_view()         , name='project_update'),
    path('projects/<int:pk>/delete/'                    , project_views.ProjectDelete.as_view()         , name='project_delete'),

]