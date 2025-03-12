from django.urls import path
from .views import MetadataElementsJsonView

urlpatterns = [
    path("metadata/autocomplete/<str:el_type>/", MetadataElementsJsonView.as_view(), name="metadata-autocomplete")
]
