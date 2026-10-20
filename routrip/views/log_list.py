from django.views.generic import ListView
from django.db.models import Q
from ..models import Log


class LogListView(ListView):
    """
    ログ一覧ビュー
    """

    model = Log
    paginate_by = 10
    context_object_name = 'logs'
    template_name = 'routrip/top_page.html'

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-posted_at')

        departure=self.request.GET.get('departure','').strip()
        destination=self.request.GET.get('destination','').strip()
        tag_query=self.request.GET.get('tag','').strip()

        #出発地キーワードでの絞り込み
        if departure:
            queryset = queryset.filter(
                Q(title__icontains=departure) | Q(start_spot__name__icontains=departure)
            )

        #目的地キーワードでの絞り込み
        if destination:
            queryset = queryset.filter(
                Q(title__icontains=destination) | Q(cards__spot__name__icontains=destination)
            ).distinct()#重複を排除するため

        #タグ名での絞り込み
        if tag_query:
            tag_list  = tag_query.split()
            for tag in tag_list:
                queryset=queryset.filter(
                    tags__name__icontains=tag
                )
            queryset = queryset.distinct() # 複数条件による重複を防ぐため    


        return queryset

    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        departure = self.request.GET.get('departure','').strip()
        destination = self.request.GET.get('destination','').strip()   
        tag_query=self.request.GET.get('tag','').strip()


        #検索ワードを保持・判定する
        context['departure'] = departure
        context['destination'] = destination
        context['tag']=tag_query#検索後も入力欄に残す
        context['is_searched'] = bool(departure or destination or tag_query)

        return context

    