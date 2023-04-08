from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from ranker.models import Template, TemplateItem, AIModel, Project, Domain
from accounts.models import User

class Command(BaseCommand):
    help = "Initialize a few templates and templates when a fresh environment launches"

    # def add_arguments(self, parser):
    #     parser.add_argument('file_path', nargs=1, type=str) 
        #This is a positional argument, which, since added first, evaluates the first word to come after the command
        # The nargs='+' command says to take every word in the command and combine it together into a list and error if no words are found

    def handle(self, *args, **options):
        #handle is a special method that the django manage command will run, with the args and options provided

        if Template.objects.count() > 0:
            self.stderr.write(f"There are already {Template.objects.count()} templates in the database. Skipping creation.")
            return

        ai_model = AIModel(
            ai_model = "ChatGPT 3.5",
            api_identifier = "gpt-3.5-turbo"
        )
        ai_model.save()

        user = User( username='sample_user', first_name='Test', last_name='User', email='test@example.com')
        user.save()
        user.set_password('samplepass')

        project = Project( project='Structured Domain Information')
        project.save()

        project.user.add(user)

        domain = Domain.objects.get(domain='fanatics.com')
        project.domain.add(domain)

        domain = Domain.objects.get(domain='hayneedle.com')
        project.domain.add(domain)

        domain = Domain.objects.get(domain='nastygal.com')
        project.domain.add(domain)

        domain = Domain.objects.get(domain='teladoc.com')
        project.domain.add(domain)

        domain = Domain.objects.get(domain='healthline.com')
        project.domain.add(domain)

        market_research = Template(
            template = "Market Research",
            scope = "per_domain",
        )
        market_research.save()
        
        competitive_analysis = Template(
            template = "Competitive Analysis",
            scope = "per_domain",
        )
        competitive_analysis.save()

        domain_data = Template(template = "Domain Data", scope = "per_domain",)
        domain_data.save()

        project_template = Template(template = "Structured Data", scope = "per_domain", project = project,)
        project_template.save()

        #Domain Data Template Items
        template_item = TemplateItem(prompt1 = "For @currentDomain, provide their Business Name, 6-digit NAICS code, Brands, Domains of Competitors, Products in a simple JSON object. In your response, use \"business_name\", \"naics_6\", \"company_brands\", \"competitor_domains\", and \"company_products\" as keys in the JSON.",
            order = 1,
            template = domain_data,
        )
        template_item.save()

        #Market Research Product Templates
        template_item = TemplateItem(
            prompt1 = "Conduct a SWOT analysis for @currentDomain and present results in a table",
            order = 1,
            template = market_research,
        )
        template_item.save()

        template_item = TemplateItem(
            prompt1 = "Conduct a five forces analysis for @currentDomain",
            order = 2,
            template = market_research,
        )
        template_item.save()
        
        template_item = TemplateItem(
            prompt1 = "What could be some buyer personas for @currentDomain",
            order = 3,
            template = market_research,
        )
        template_item.save()
                
        template_item = TemplateItem(
            prompt1 = "What are some strategies for @currentDomain to increase their revenue? For each of these strategies, suggest one specific, detailed, tactic they could take and if appropriate a vendor that could help implement this tactic",
            order = 4,
            template = market_research,
        )
        template_item.save()
                
        template_item = TemplateItem(
            prompt1 = "What are some strategies for @currentDomain to reduce their costs? For each of these strategies, suggest one specific, detailed, tactic they could take and if appropriate a vendor that could help implement this tactic",
            order = 5,
            template = market_research,
        )
        template_item.save()
                
        template_item = TemplateItem(
            prompt1 = "What are some ideas for @currentDomain to improve their processes? For each of these strategies, suggest one specific, detailed, tactic they could take and if appropriate a vendor that could help implement this tactic",
            order = 6,
            template = market_research,
        )
        template_item.save()
                
        template_item = TemplateItem(
            prompt1 = "What are some ideas for @currentDomain to improve their employee experience? For each of these strategies, suggest one specific, detailed, tactic they could take and if appropriate a vendor that could help implement this tactic",
            order = 7,
            template = market_research,
        )
        template_item.save()

        #Product Templates for Competitive Analysis

                        
        template_item = TemplateItem(
            prompt1 = "Who are the main competitors of @currentDomain?",
            order = 1,
            template = competitive_analysis,
        )
        template_item.save()
                                
        template_item = TemplateItem(
            prompt1 = "What templates or services do the main competitors of @currentDomain offer",
            order = 2,
            template = competitive_analysis,
        )
        template_item.save()
                                
        template_item = TemplateItem(
            prompt1 = "Can you compare the features of @currentDomain to the features of its competitors",
            order = 3,
            template = competitive_analysis,
        )
        template_item.save()
                                        
        template_item = TemplateItem(
            prompt1 = "Can you compare the marketing strategy of @currentDomain to the marketing strategy of its competitors",
            order = 4,
            template = competitive_analysis,
        )
        template_item.save()
                                        
        template_item = TemplateItem(
            prompt1 = "Which of @currentDomain's competitors has a unique distribution strategy",
            order = 5,
            template = competitive_analysis,
        )
        template_item.save()
                                        
        template_item = TemplateItem(
            prompt1 = "Can you provide information on the reputations of each of @currentDomain's competitors",
            order = 6,
            template = competitive_analysis,
        )
        template_item.save()
                                                
        template_item = TemplateItem(
            prompt1 = "Which of @currentDomain's competitors has exceptional customer support?",
            order = 7,
            template = competitive_analysis,
        )
        template_item.save()
                                                
        template_item = TemplateItem(
            prompt1 = "What opportunities could @currentDomain take advantage of?",
            order = 8,
            template = competitive_analysis,
        )
        template_item.save()
                                                
        template_item = TemplateItem(
            prompt1 = "What threats should @currentDomain be on the lookout for?",
            order = 9,
            template = competitive_analysis,
        )
        template_item.save()
                                                
        template_item = TemplateItem(
            prompt1 = "What are some gaps in the market that @currentDomain could explore?",
            order = 10,
            template = competitive_analysis,
        )
        template_item.save()
                                                  
        template_item = TemplateItem(
            prompt1 = "What might be the long-term strategy of each of @currentDomain's competitors?",
            order = 11,
            template = competitive_analysis,
        )
        template_item.save()
                                                          
        template_item = TemplateItem(
            prompt1 = "Which companies could @currentDomain acquire to address emerging trends in the industry?",
            order = 12,
            template = competitive_analysis,
        )
        template_item.save()

        # Template items for project template

        template_item = TemplateItem(
            prompt1 = "What is the business name, industry, largest competitor, and closest competitor of @currentDomain",
            order = 1,
            template = project_template,
        )
        template_item.save()

        template_item = TemplateItem(
            prompt1 = "What is the business name, industry, largest competitor, and closest competitor of @currentDomain. Please provide results in a table format.",
            order = 1,
            template = project_template,
        )
        template_item.save()

        template_item = TemplateItem(
            prompt1 = "What is the business name, industry, largest competitor, and closest competitor of @currentDomain. Please provide results in a list with “Business Name:”, “Industry:”, “Largest Competitor:”, and “Closest Competitor:” at the beginning of each item.",
            order = 1,
            template = project_template,
        )
        template_item.save()

        template_item = TemplateItem(
            prompt1 = "What is the business name, industry, largest competitor, and closest competitor of @currentDomain. See an example: Business Name: Wayfair Industry: Home Furnishings Largest Competitor: Amazon Closest Competitor: Hayneedle",
            order = 1,
            template = project_template,
        )
        template_item.save()

        print(f"After startproducts, there are now {Template.objects.count()} templates and {TemplateItem.objects.count()} template items.")
