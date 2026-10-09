from django.views.generic import ListView
from django.db.models import Q
from ..models import Log


class LogListView(ListView):
    model = Log
    paginate_by = int
    context_object_name = 'logs'
    template_name = 'routrip/top_page.html'

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-created_at')

        departure=self.request.GET.get('departure').strip()
        destination=self.request.GET.get('destination').strip()

        #出発地キーワードでの絞り込み
        if departure:
            queryset = queryset.filter(
                Q(title_icon__icontains=departure) | Q(departure__icontains=departure)
            )

        #目的地キーワードでの絞り込み
        if destination:
            queryset = queryset.filter(
                Q(title_icon__icontains=destination) | Q(destination__icontains=destination)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        departure = self.request.GET.get('departure','').strip()
        destination = self.request.GET.get('destination','').strip()   

        #検索ワードを保持・判定する
        context['departure'] = departure
        context['destination'] = destination
        context['is_searched'] = bool(departure or destination)  
        return context

    