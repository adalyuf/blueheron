from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.db.models import UniqueConstraint
from accounts.models import User 
# Create your models here.

class Domain(models.Model):
    domain = models.CharField(max_length=200, unique=True)
    keywords = models.BigIntegerField(null=True)
    traffic = models.BigIntegerField(null=True)
    cost = models.DecimalField(max_digits=19, decimal_places=2,null=True)
    rank = models.IntegerField(null=True)
    ad_keywords = models.BigIntegerField(null=True)
    ad_traffic = models.BigIntegerField(null=True)
    ad_cost = models.DecimalField(max_digits=19, decimal_places=2,null=True)
    adult_content = models.BooleanField(default=False)
    def __str__(self):
        return self.domain
    
    class Meta:
        ordering = ['rank']

def keyword_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    d = Domain.objects.get(pk=instance.domain_id)
    t = timezone.now()
    filename = f"{d.id}-{d.domain}-{t.year}-{t.month}-{t.day}-{t.hour}-{t.minute}-{t.second}.csv"
    return f"documents/{d.id}-{d.domain}/{filename}"

class KeywordFile(models.Model):
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE)
    filepath = models.FileField(upload_to=keyword_directory_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    primary = models.BooleanField(default=False)
    def __str__(self):
        return self.filepath
    
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
    
class ProjectDomain(models.Model):
    project = models.ForeignKey(Project , on_delete=models.CASCADE)
    domain  = models.ForeignKey(Domain  , on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.project}: {self.domain}"
    
class Template(models.Model):
    scope_choices = [
        ('global', 'global'),
        ('per_domain', 'per_domain')
    ]
    template = models.CharField(max_length=200, unique=True)
    scope = models.CharField(max_length=200,choices=scope_choices, default='per_domain')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)
    helper_text_before = models.TextField(null=True)
    helper_text_after = models.TextField(null=True)
    def __str__(self):
        return self.template

class TemplateItem(models.Model):
    prompt1 = models.TextField()
    token1 = models.ForeignKey(TokenType, on_delete=models.SET_NULL, null=True, blank=True)
    prompt2 = models.CharField(max_length=200, null=True, blank=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    order = models.IntegerField(default=100)
    visible = models.BooleanField(default=True)
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    def __str__(self):
        return self.prompt1
    
    class Meta:
        ordering = ['template', 'order']

class Conversation(models.Model):
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(null=True)
    answered_at = models.DateTimeField(null=True)
    class Meta:
        constraints = [ 
            UniqueConstraint(name='unique_template_domain', fields=['template', 'domain', 'project', 'ai_model'], include=['answered_at']),
        ]
    def __str__(self):
        return f"{self.template.template}: {self.domain.domain}"


class Message(models.Model):
    prompt = models.TextField()
    title = models.CharField(max_length=200, null=True)
    response = models.TextField(null=True)
    formatted_response = models.TextField(null=True)
    visible = models.BooleanField(default=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    order = models.IntegerField(default=100)
    requested_at = models.DateTimeField(null=True)
    answered_at = models.DateTimeField(null=True)
    def __str__(self):
        return self.prompt 
    
    class Meta:
        ordering = ['order']