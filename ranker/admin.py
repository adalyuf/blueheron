from django.contrib import admin

# Register your models here.
from .models import Domain, KeywordFile, Product, ProductTemplate, Conversation, Message

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ( 'domain', 'keywords', 'cost', 'rank', 'adult_content')
    fields = ['domain', 'rank', 'adult_content', ('keywords', 'traffic', 'cost'), ('ad_keywords', 'ad_traffic', 'ad_cost')]

@admin.register(KeywordFile)
class KeywordFileAdmin(admin.ModelAdmin):
    list_display = ('domain', 'filepath', 'uploaded_at', 'primary')

class PTInline(admin.TabularInline):
    model = ProductTemplate
    extra = 0

@admin.register(Product)
class ThisDoesntMatter(admin.ModelAdmin):
    list_display = ('product', 'scope')
    inlines = [PTInline]

@admin.register(ProductTemplate)
class PTAdmin(admin.ModelAdmin):
    list_display = ( 'prompt1', 'token1', 'prompt2', 'title', 'order', 'visible', 'product',)
    list_filter = ('product',)

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('product', 'domain', 'requested_at', 'answered_at')
    inlines = [MessageInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ( 'prompt', 'title', 'visible', 'order', 'answered_at', 'conversation')