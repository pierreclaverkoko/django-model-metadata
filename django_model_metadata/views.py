from django.views import View
from django.http import JsonResponse

from .model_mixins import GENERAL_FK_MODELS, ON_DELETE_CHOICES


class MetadataElementsJsonView(View):
    def get(self, request, el_type):
        query = self.request.GET.get("query", "")
        if el_type == "models":
            return JsonResponse(
                {
                    "results": [
                        {"title": model[1], "value": model[0]}
                        for model in GENERAL_FK_MODELS
                        if query.lower() in model[0].lower()
                    ]
                }
            )
        elif el_type == "on_delete":
            return JsonResponse(
                {
                    "results": [
                        {"title": model[1], "value": model[0]}
                        for model in ON_DELETE_CHOICES
                        if query.lower() in model[0].lower()
                    ]
                }
            )
        else:
            return JsonResponse({"results": []})
