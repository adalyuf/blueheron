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
            prompt1 = "What are some strategies for @currentDomain to increase their revenue? For each of these strategies, suggest one specific, detailed, tactic they could take and if appropriate a vendor that could help implement this tactic",
            order = 4,
            product = market_research,
        )
        pt.save()
                
        pt = ProductTemplate(
            prompt1 = "What are some strategies for @currentDomain to reduce their costs? For each of these strategies, suggest one specific, detailed, tactic they could take and if appropriate a vendor that could help implement this tactic",
            order = 5,
            product = market_research,
        )
        pt.save()
                
        pt = ProductTemplate(
            prompt1 = "What are some ideas for @currentDomain to improve their processes? For each of these strategies, suggest one specific, detailed, tactic they could take and if appropriate a vendor that could help implement this tactic",
            order = 6,
            product = market_research,
        )
        pt.save()
                
        pt = ProductTemplate(
            prompt1 = "What are some ideas for @currentDomain to improve their employee experience? For each of these strategies, suggest one specific, detailed, tactic they could take and if appropriate a vendor that could help implement this tactic",
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
            prompt1 = "Can you compare the features of @currentDomain to the features of its competitors",
            order = 3,
            product = competitive_analysis,
        )
        pt.save()
                                        
        pt = ProductTemplate(
            prompt1 = "Can you compare the marketing strategy of @currentDomain to the marketing strategy of its competitors",
            order = 4,
            product = competitive_analysis,
        )
        pt.save()
                                        
        pt = ProductTemplate(
            prompt1 = "Which of @currentDomain's competitors has a unique distribution strategy",
            order = 5,
            product = competitive_analysis,
        )
        pt.save()
                                        
        pt = ProductTemplate(
            prompt1 = "Can you provide information on the reputations of each of @currentDomain's competitors",
            order = 6,
            product = competitive_analysis,
        )
        pt.save()
                                                
        pt = ProductTemplate(
            prompt1 = "Which of @currentDomain's competitors has exceptional customer support?",
            order = 7,
            product = competitive_analysis,
        )
        pt.save()
                                                
        pt = ProductTemplate(
            prompt1 = "What opportunities could @currentDomain take advantage of?",
            order = 8,
            product = competitive_analysis,
        )
        pt.save()
                                                
        pt = ProductTemplate(
            prompt1 = "What threats should @currentDomain be on the lookout for?",
            order = 9,
            product = competitive_analysis,
        )
        pt.save()
                                                
        pt = ProductTemplate(
            prompt1 = "What are some gaps in the market that @currentDomain could explore?",
            order = 10,
            product = competitive_analysis,
        )
        pt.save()
                                                  
        pt = ProductTemplate(
            prompt1 = "What might be the long-term strategy of each of @currentDomain's competitors?",
            order = 11,
            product = competitive_analysis,
        )
        pt.save()
                                                          
        pt = ProductTemplate(
            prompt1 = "Which companies could @currentDomain acquire to address emerging trends in the industry?",
            order = 12,
            product = competitive_analysis,
        )
        pt.save()

        print(f"After startproducts, there are now {Product.objects.count()} products and {ProductTemplate.objects.count()} product templates.")
