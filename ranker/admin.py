from django.contrib import admin

# Register your models here.
from .models import Domain, KeywordFile, Template, TemplateItem, Conversation, Message, AIModel, Project, ProjectUser, ProjectDomain

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ( 'domain', 'keywords', 'cost', 'rank', 'adult_content')
    fields = ['domain', 'rank', 'adult_content', ('keywords', 'traffic', 'cost'), ('ad_keywords', 'ad_traffic', 'ad_cost')]

@admin.register(KeywordFile)
class KeywordFileAdmin(admin.ModelAdmin):
    list_display = ('domain', 'filepath', 'uploaded_at', 'primary')

class TemplateItemInlineAdmin(admin.TabularInline):
    model = TemplateItem
    extra = 0

@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ('template', 'scope', 'project')
    inlines = [TemplateItemInlineAdmin]

@admin.register(TemplateItem)
class TemplateItemAdmin(admin.ModelAdmin):
    list_display = ( 'prompt1', 'token1', 'prompt2', 'title', 'order', 'visible', 'template',)
    list_filter = ('template',)

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('template', 'domain', 'requested_at', 'answered_at', 'ai_model')
    inlines = [MessageInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ( 'prompt', 'title', 'visible', 'order', 'answered_at', 'conversation')

@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ('ai_model', 'api_identifier')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project', 'requests_used')

@admin.register(ProjectUser)
class ProjectUserAdmin(admin.ModelAdmin):
    list_display = ('project', 'user')

@admin.register(ProjectDomain)
class ProjectDomainAdmin(admin.ModelAdmin):
    list_display = ('project', 'domain')