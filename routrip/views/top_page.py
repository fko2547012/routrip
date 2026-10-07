from django.views.generic.base import TemplateView

class TopPageView(TemplateView):
    template_name = 'routrip/top_page.html'