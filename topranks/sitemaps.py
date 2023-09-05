from django.contrib.sitemaps import Sitemap
from ranker.models import Domain, Keyword


class KeywordsSitemap(Sitemap):
    def items(self):
        return Keyword.objects.filter(answered_at__isnull=False).exclude(keyword__exact=None).exclude(keyword__exact='')
    
    def lastmod(self, obj):
        return obj.updated_at
    
    protocol = 'https'
    limit = 10000