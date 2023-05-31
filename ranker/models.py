from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.db.models import UniqueConstraint, Max 
from django.core.validators import FileExtensionValidator, RegexValidator
from accounts.models import User 
# Create your models here.

def alphanumeric_validator():
    return RegexValidator(r'^[a-zA-Z0-9-_ ]+$',
        'Only numbers, letters, underscores, dashes and spaces are allowed.')

class Domain(models.Model):
    domain  = models.CharField(max_length=200, unique=True)
    rank    = models.IntegerField(null=True, default=999999)
    keywords    = models.BigIntegerField(null=True, blank=True)
    traffic     = models.BigIntegerField(null=True, blank=True)
    cost        = models.DecimalField(max_digits=19, decimal_places=2,null=True, blank=True)
    ad_keywords = models.BigIntegerField(null=True, blank=True)
    ad_traffic  = models.BigIntegerField(null=True, blank=True)
    ad_cost     = models.DecimalField(max_digits=19, decimal_places=2,null=True, blank=True)
    adult_content = models.BooleanField(default=False)
    business_json = models.JSONField(null=True, blank=True)
    business_name = models.CharField(max_length=200, null=True, blank=True)
    business_attempts = models.IntegerField(default=0)
    business_retrieved_at = models.DateTimeField(default=None, null=True)
    business_api_response = models.TextField(null=True, blank=True)
    naics_6       = models.CharField(max_length=20, null=True, blank=True)
    competitors = models.ManyToManyField(
        'self',
        through="Competition",
        through_fields=("domain", "competitor"),
    )
    def __str__(self):
        return self.domain
    def get_absolute_url(self):
        return reverse('domain_detail', args=[str(self.id)])
    
    class Meta:
        ordering = ['rank']

class Brand(models.Model):
    type_choices = [
        ('brand', 'brand'),
        ('product', 'product'),
        ('competitor_brand', 'competitor_brand'),
        ('competitor_product', 'competitor_product'),
    ]
    domain = models.ForeignKey(Domain , on_delete=models.CASCADE)
    brand = models.CharField(max_length=200)
    type = models.CharField(max_length=200, choices=type_choices, default='brand')
    def __str__(self):
        return f"{self.domain}: {self.brand}"
    def get_absolute_url(self):
        return reverse('domain_detail', args=[str(self.domain.id)])
    def kwcount(self):
        return Keyword.objects.filter(answered_at__isnull=False).filter(ai_answer__icontains=self.brand).count()

class Competition(models.Model):
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='source_domain_set')
    competitor = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='competitor_set')
    def __str__(self):
        return f"{self.domain}: {self.competitor}"

def keyword_directory_path(instance, filename=None):
    d = Domain.objects.get(pk=instance.domain_id)
    t = timezone.now()
    filename = f"{d.id}-{d.domain}-{t.year}-{t.month}-{t.day}-{t.hour}-{t.minute}-{t.second}.csv"
    return f"documents/{d.id}-{d.domain}/{filename}"

class KeywordFile(models.Model):
    domain      = models.ForeignKey(Domain, on_delete=models.CASCADE)
    filepath    = models.FileField(upload_to=keyword_directory_path, validators=[FileExtensionValidator(allowed_extensions=["csv"])])
    uploaded_at = models.DateTimeField(auto_now_add=True)
    primary     = models.BooleanField(default=False)
    processed_at = models.DateTimeField(default=None, null=True)
    def __str__(self):
        return self.filepath.name
    def get_absolute_url(self):
        return reverse('domain_detail', args=[str(self.domain.id)])
    
class TokenType(models.Model):
    type = models.CharField(max_length=200, unique=True)
    def __str__(self):
        return self.type

class Token(models.Model):
    value = models.CharField(max_length=200)
    type = models.ForeignKey(TokenType, on_delete=models.CASCADE)
    def __str__(self):
        return self.value

class AIModel(models.Model):
    ai_model = models.CharField(max_length=200)
    api_identifier = models.CharField(max_length=200, null=True)
    def __str__(self):
        return self.ai_model 

class Project(models.Model):
    project = models.CharField(max_length=200)
    requests_used = models.IntegerField(default=0)
    user = models.ManyToManyField(
        User,
        through='ProjectUser',
        through_fields=('project', 'user'),
    )
    domain = models.ManyToManyField(
        Domain,
        through='ProjectDomain',
        through_fields=('project', 'domain'),
    )
    def __str__(self):
        return self.project
    def get_absolute_url(self):
        """Returns the URL to access a particular instance of the model."""
        return reverse('project_detail', args=[str(self.id)])

class ProjectUser(models.Model):
    project = models.ForeignKey(Project , on_delete=models.CASCADE)
    user    = models.ForeignKey(User    , on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.project}: {self.user}"
    def get_absolute_url(self):
        return reverse('project_settings', args=[str(self.project.id)])
    
class ProjectDomain(models.Model):
    project = models.ForeignKey(Project , on_delete=models.CASCADE, validators=[alphanumeric_validator()])
    domain  = models.ForeignKey(Domain  , on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.project}: {self.domain}"
    def get_absolute_url(self):
        return reverse('project_settings', args=[str(self.project.id)])
    
class Template(models.Model):
    scope_choices = [
        ('global', 'global'),
        ('per_domain', 'per_domain')
    ]
    template    = models.CharField(max_length=200, unique=True, validators=[alphanumeric_validator()])
    scope       = models.CharField(max_length=200, choices=scope_choices, default='per_domain')
    project     = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    helper_text_before  = models.TextField(null=True, blank=True)
    helper_text_after   = models.TextField(null=True, blank=True)
    def __str__(self):
        return self.template
    def get_absolute_url(self):
        return reverse('template_detail', args=[str(self.id)])
    

class TemplateItem(models.Model):
    mode_choices = [
        ('markdown', 'markdown'),
        ('json', 'json')
    ]
    prompt1     = models.TextField()
    token1      = models.ForeignKey(TokenType, on_delete=models.SET_NULL, null=True, blank=True)
    prompt2     = models.CharField(max_length=200, null=True, blank=True)
    title       = models.CharField(max_length=200, null=True, blank=True)
    order       = models.IntegerField(default=100)
    visible     = models.BooleanField(default=True)
    template    = models.ForeignKey(Template, on_delete=models.CASCADE)
    mode        = models.CharField(max_length=200, choices=mode_choices, default='markdown')
    def __str__(self):
        return self.prompt1
    def get_absolute_url(self):
        return reverse('template_detail', args=[str(self.template.id)])
    
    class Meta:
        ordering = ['template', 'order']

class Conversation(models.Model):
    template    = models.ForeignKey(Template, on_delete=models.CASCADE)
    domain      = models.ForeignKey(Domain, on_delete=models.CASCADE, null=True)
    project     = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)
    ai_model    = models.ForeignKey(AIModel, on_delete=models.CASCADE)
    requested_at= models.DateTimeField(null=True)
    answered_at = models.DateTimeField(null=True)
    class Meta:
        constraints = [ 
            UniqueConstraint(name='unique_template_domain', fields=['template', 'domain', 'project', 'ai_model'], include=['answered_at']),
        ]
    def __str__(self):
        return f"{self.template.template}: {self.domain.domain}"
    def get_absolute_url(self):
        return reverse('conversation_detail', args=[str(self.id)])


class Message(models.Model):
    prompt  = models.TextField()
    title   = models.CharField(max_length=200, null=True)
    response = models.TextField(null=True, blank=True)
    markdown_response = models.TextField(null=True, blank=True)
    json_response   = models.JSONField(null=True)
    visible         = models.BooleanField(default=True)
    conversation    = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    order           = models.IntegerField(default=100)
    requested_at    = models.DateTimeField(null=True)
    answered_at     = models.DateTimeField(null=True)
    template_item   = models.ForeignKey(TemplateItem, on_delete=models.SET_NULL, null=True)
    def __str__(self):
        return self.prompt
    def get_absolute_url(self):
        return reverse('conversation_edit', args=[str(self.conversation.id)])
    
    class Meta:
        ordering = ['order']

class Keyword(models.Model):
    keyword                     = models.CharField(max_length=200, unique=True)
    user_intent                 = models.TextField(null=True)
    natural_language_question   = models.TextField(null=True)
    ai_answer                   = models.TextField(null=True)
    likely_previous_queries     = models.JSONField(null=True)
    likely_next_queries         = models.JSONField(null=True)
    requested_at                = models.DateTimeField(null=True)
    answered_at                 = models.DateTimeField(null=True)
    json_response               = models.JSONField(null=True)
    def __str__(self):
        return self.keyword
    
class KeywordPosition(models.Model):
    domain  = models.ForeignKey(Domain, on_delete=models.SET_NULL, null=True)
    keyword = models.ForeignKey(Keyword, on_delete=models.SET_NULL, null=True)
    domain_text         = models.TextField()
    keyword_text        = models.TextField()
    position            = models.IntegerField(null=True)
    previous_position   = models.IntegerField(null=True)
    search_volume       = models.IntegerField(null=True)
    keyword_difficulty  = models.IntegerField(null=True)
    cpc                 = models.DecimalField(max_digits=19, decimal_places=2,null=True)
    url                 = models.TextField(null=True)
    traffic             = models.IntegerField(null=True)
    traffic_percent     = models.DecimalField(max_digits=19, decimal_places=2,null=True)
    traffic_cost        = models.DecimalField(max_digits=19, decimal_places=2,null=True)
    competitive_difficulty = models.DecimalField(max_digits=19, decimal_places=2,null=True)
    results             = models.BigIntegerField(null=True)
    trends              = models.TextField(null=True)
    retrieved_at        = models.DateTimeField(null=True)
    serp                = models.TextField(null=True)
    intents             = models.TextField(null=True)
    type                = models.TextField(null=True)
    def __str__(self):
        return f"{self.keyword} - {self.domain} - {self.position}"