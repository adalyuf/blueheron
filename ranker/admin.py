from django.contrib import admin

# Register your models here.
from .models import Domain, KeywordFile, Template, TemplateItem, Conversation, Message, AIModel, Project, ProjectUser, ProjectDomain, Keyword, KeywordPosition, Brand, BrandDomain, Competition

class BrandInlineAdmin(admin.TabularInline):
    model = BrandDomain
    extra = 0
    readonly_fields=['brand', 'type',]

class CompetitionInlineAdmin(admin.TabularInline):
    model = Competition
    extra = 0
    readonly_fields = ['competitor',]
    fk_name = 'domain'

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ( 'domain', 'keywords', 'cost', 'rank', 'adult_content')
    fields = ['domain', 'rank', 'adult_content', ('keywords', 'traffic', 'cost'), ('ad_keywords', 'ad_traffic', 'ad_cost'), 'business_json', 'business_name', 'naics_6']
    search_fields = ['domain']
    list_filter = ['business_retrieved_at', 'business_attempts', ('business_json', admin.EmptyFieldListFilter)]
    inlines = [BrandInlineAdmin, CompetitionInlineAdmin]

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ( 'brand',)
    search_fields = ['brand']
    list_filter = ['keyword_indexed_at']

@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('domain', 'competitor')

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
    list_display = ( 'prompt1', 'token1', 'prompt2', 'title', 'order', 'visible', 'template', 'mode')
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

@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'user_intent', 'likely_previous_queries', 'likely_next_queries', 'requested_at', 'answered_at')
    list_filter = ('answered_at',)
    search_fields = ['keyword', 'ai_answer', 'likely_previous_queries', 'likely_next_queries']
    
@admin.register(KeywordPosition)
class KeywordPositionAdmin(admin.ModelAdmin):
    list_display = ('keyword_text', 'domain_text', 'keyword', 'domain', 'position')