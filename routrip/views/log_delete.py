from django.urls import reverse_lazy
from django.views.generic import DeleteView
from ..models import Log

class LogDeleteView(DeleteView):
    model = Log
    template_name = "routrip/log_delete.html"
    context_object_name = 'log'
    success_url = reverse_lazy("routrip:mypage")

    def get_queryset(self):
        return Log.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # このログに関連するスポットを退避
        spots = set()
        spots.add(self.object.start_spot)
        for card in self.object.cards.all():
            spots.add(card.spot)
        for section in self.object.sections.all():
            spots.add(section.from_spot)
            spots.add(section.to_spot)

        # ログ削除
        response = super().delete(request, *args, **kwargs)

        # Spot削除
        for spot in spots:
            if (
                spot.start_logs.count() == 0
                and spot.log_cards.count() == 0
                and spot.departing_sections.count() == 0
                and spot.arriving_sections.count() == 0
            ):
                spot.delete()

        return response