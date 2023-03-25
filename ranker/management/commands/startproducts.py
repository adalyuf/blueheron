from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from ranker.models import Product, ProductTemplate

class Command(BaseCommand):
    help = "Initialize a few products and templates when a fresh environment launches"

    # def add_arguments(self, parser):
    #     parser.add_argument('file_path', nargs=1, type=str) 
        #This is a positional argument, which, since added first, evaluates the first word to come after the command
        # The nargs='+' command says to take every word in the command and combine it together into a list and error if no words are found

    def handle(self, *args, **options):
        #handle is a special method that the django manage command will run, with the args and options provided

        if Product.objects.count() > 0:
            self.stderr.write(f"There are already {Product.objects.count()} products in the database. Skipping creation.")
            return

        market_research = Product(
            product = "Market Research",
            scope = "per_domain",
        )
        market_research.save()
        
        competitive_analysis = Product(
            product = "Competitive Analysis",
            scope = "per_domain",
        )
        competitive_analysis.save()

        #Market Research Product Templates
        pt = ProductTemplate(
            prompt1 = "Conduct a SWOT analysis for @currentDomain and present results in a table",
            order = 1,
            product = market_research,
        )
        pt.save()

        pt = ProductTemplate(
            prompt1 = "Conduct a five forces analysis for @currentDomain",
            order = 2,
            product = market_research,
        )
        pt.save()
        
        pt = ProductTemplate(
            prompt1 = "What could be some buyer personas for @currentDomain",
            order = 3,
            product = market_research,
        )
        pt.save()
                
        pt = ProductTemplate(
            prompt1 = "What are some strategies for @currentDomain to increase their revenue? For each of these strategies, suggest one specific, detailed, tactic they could take",
            order = 4,
            product = market_research,
        )
        pt.save()
                
        pt = ProductTemplate(
            prompt1 = "What are some strategies for @currentDomain to reduce costs? For each of these strategies, suggest one specific, detailed, tactic they could take",
            order = 5,
            product = market_research,
        )
        pt.save()
                
        pt = ProductTemplate(
            prompt1 = "What are some ideas for @currentDomain to improve their processes? For each of these ideas, recommend a few companies that help companies of their size and industry implement these ideas",
            order = 6,
            product = market_research,
        )
        pt.save()
                
        pt = ProductTemplate(
            prompt1 = "What are some ideas for @currentDomain improve their employee experience",
            order = 7,
            product = market_research,
        )
        pt.save()

        #Product Templates for Competitive Analysis

                        
        pt = ProductTemplate(
            prompt1 = "Who are the main competitors of @currentDomain?",
            order = 1,
            product = competitive_analysis,
        )
        pt.save()
                                
        pt = ProductTemplate(
            prompt1 = "What products or services do the main competitors of @currentDomain offer",
            order = 2,
            product = competitive_analysis,
        )
        pt.save()
                                
        pt = ProductTemplate(
            prompt1 = "If I run @currentDomain, How does my product or service compare to my competitors' offerings in terms of features, quality, and price?",
            order = 3,
            product = competitive_analysis,
        )
        pt.save()
                                        
        pt = ProductTemplate(
            prompt1 = "If I run @currentDomain, How do my competitors market their products or services?",
            order = 4,
            product = competitive_analysis,
        )
        pt.save()
                                        
        pt = ProductTemplate(
            prompt1 = "If I run @currentDomain, How do my competitors distribute their products or services?",
            order = 5,
            product = competitive_analysis,
        )
        pt.save()
                                        
        pt = ProductTemplate(
            prompt1 = "If I run @currentDomain, What is my competitors' reputation in the industry?",
            order = 6,
            product = competitive_analysis,
        )
        pt.save()
                                                
        pt = ProductTemplate(
            prompt1 = "If I run @currentDomain, How do my competitors handle customer service and support?",
            order = 7,
            product = competitive_analysis,
        )
        pt.save()
                                                
        pt = ProductTemplate(
            prompt1 = "If I run @currentDomain, What are the opportunities and threats that my competitors pose to my business?",
            order = 8,
            product = competitive_analysis,
        )
        pt.save()
                                                
        pt = ProductTemplate(
            prompt1 = "If I run @currentDomain, What are the gaps in the market that my competitors have not yet addressed?",
            order = 9,
            product = competitive_analysis,
        )
        pt.save()
                                                
        pt = ProductTemplate(
            prompt1 = "If I run @currentDomain, What are the emerging trends in the industry that my competitors are not taking advantage of?",
            order = 10,
            product = competitive_analysis,
        )
        pt.save()
                                                  
        pt = ProductTemplate(
            prompt1 = "If I run @currentDomain, what might be some of my competitors' long-term goals and how might they work to achieve them?",
            order = 11,
            product = competitive_analysis,
        )
        pt.save()

        print(f"After startproducts, there are now {Product.objects.count()} products and {ProductTemplate.objects.count()} product templates.")
