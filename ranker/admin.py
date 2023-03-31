from django.contrib import admin

# Register your models here.
from .models import Domain, KeywordFile, Template, TemplateItem, Conversation, Message

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
    list_display = ('template', 'scope')
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
    list_display = ('template', 'domain', 'requested_at', 'answered_at')
    inlines = [MessageInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ( 'prompt', 'title', 'visible', 'order', 'answered_at', 'conversation')