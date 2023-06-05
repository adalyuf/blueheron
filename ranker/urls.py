from django.urls import path
from ranker import views
from ranker.domains import views as domain_views
from ranker.conversations import views as conv_views
from ranker.projects import views as project_views
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path("", domain_views.DomainListView.as_view(), name="home"),

    path('dashboard/', views.DashboardsView.as_view(template_name = 'pages/dashboards/index.html'), name='dashboard'),

    path("domains/"                                 , domain_views.DomainListView.as_view()     , name="domain_list"),
    path("domain_search/"                           , domain_views.domain_search                , name="domain_search"),
    path('domains/<int:domain_id>/'                 , domain_views.domain_detail                , name='domain_detail'),
    path('domains/validate_domains/'                , domain_views.validate_domains             , name='validate_domains'),

    path('keywordfile_make_primary/<int:domain_id>/<int:keywordfile_id>/'   , login_required(domain_views.keywordfile_make_primary) , name='keywordfile_make_primary'),
    path('get_keyword_responses/'                                           , login_required(domain_views.get_keyword_responses)    , name='get_keyword_responses'),
    path('get_business_data/'                                               , login_required(domain_views.get_business_data)        , name='get_business_data'),


    path('conversations/<int:conversation_id>/'                     , login_required(conv_views.conversation_detail)                 , name='conversation_detail'),
    path('conversations/add/<int:template_id>/<int:domain_id>/<int:ai_model_id>/', login_required(conv_views.conversation_add)       , name='conversation_add'),
    path('conversations/edit/<int:conversation_id>/'                , login_required(conv_views.conversation_edit)                   , name='conversation_edit'),
    path('conversations/edit/<int:conversation_id>/update_order/'   , login_required(conv_views.conversation_update_order)           , name='conversation_update_order'),
    path('conversations/edit/<int:conversation_id>/get_responses/'  , login_required(conv_views.conversation_get_responses)          , name='conversation_get_responses'),

    path('messages/delete/<int:message_id>/'            , conv_views.message_delete, name='message_delete'),

    path("templates/"                                   , login_required(views.TemplateListView.as_view())      , name="template_list"),
    path("templates/create/"                            , login_required(views.template_create)                 , name="template_create"),
    path("templates/create/<int:project_id>/"           , login_required(views.template_create)                 , name="template_create"),
    path("templates/create_conversations/"              , login_required(views.template_create_conversations)   , name="template_create_conversations"),
    path("templates/<int:pk>/"                          , login_required(views.GetTemplateView.as_view())       , name="template_detail"),
    path("templates/delete/<int:template_id>/"          , login_required(views.template_delete)                 , name="template_delete"),
    path("templates/<int:template_id>/update_order/"    , login_required(views.template_item_order)             , name="template_item_order"),
    path("template_items/delete/<int:TemplateItem_id>/" , login_required(views.template_item_delete)            , name="template_item_delete"),

    path("projects/"                                    , login_required(project_views.ProjectListView.as_view())       , name="project_list"),
    path("projects/<int:project_id>/"                   , login_required(project_views.project_detail)                  , name="project_detail"),
    path("projects/<int:project_id>/settings/"          , login_required(project_views.project_settings)                , name="project_settings"),
    path("projects/<int:project_id>/settings/<str:setting>/", login_required(project_views.project_settings)            , name="project_settings"),
    path("projects/<int:project_id>/remove_domain/"     , login_required(project_views.project_remove_domain)           , name="project_remove_domain"),
    path("projects/<int:project_id>/remove_user/"       , login_required(project_views.project_remove_user)             , name="project_remove_user"),
    path("projects/<int:project_id>/get_responses/"     , login_required(project_views.project_get_all_responses)       , name="project_get_all_responses"),
    path('projects/create/'                             , login_required(project_views.ProjectCreate.as_view())         , name='project_create'),
    path('projects/<int:pk>/update/'                    , login_required(project_views.ProjectUpdate.as_view())         , name='project_update'),
    path('projects/<int:pk>/delete/'                    , login_required(project_views.ProjectDelete.as_view())         , name='project_delete'),

    path("keywords/"                , login_required(views.KeywordListView.as_view())       , name='keyword_list'),
    path("keywords/<int:pk>/"       , login_required(views.KeywordDetailView.as_view())     , name='keyword_detail'),
    path("keywords/keyword_search/" , login_required(views.keyword_search)                  , name="keyword_search"),
    path("keywords/reset_keyword_queue/" , login_required(views.reset_keyword_queue)        , name="reset_keyword_queue"),


]