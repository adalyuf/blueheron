from django.db import models
from django.utils import timezone
from django.db.models import UniqueConstraint

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

class Product(models.Model):
    scope_choices = [
        ('global', 'global'),
        ('per_domain', 'per_domain')
    ]
    product = models.CharField(max_length=200, unique=True)
    scope = models.CharField(max_length=200,choices=scope_choices, default='per_domain')
    def __str__(self):
        return self.product

class ProductTemplate(models.Model):
    prompt1 = models.TextField()
    token1 = models.ForeignKey(TokenType, on_delete=models.SET_NULL, null=True, blank=True)
    prompt2 = models.CharField(max_length=200, null=True, blank=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    order = models.IntegerField(default=100)
    visible = models.BooleanField(default=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    def __str__(self):
        return self.prompt1
    
    class Meta:
        ordering = ['product', 'order']

class Conversation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, null=True)
    requested_at = models.DateTimeField(null=True)
    answered_at = models.DateTimeField(null=True)
    class Meta:
        constraints = [ #Apparently SQLLite doesn't support unique constraints on anything other than primary key columns. So... this won't be enforced
            UniqueConstraint(name='unique_product_domain', fields=['product', 'domain'], include=['answered_at']),
        ]
    def __str__(self):
        return f"{self.product.product}: {self.domain.domain}"


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