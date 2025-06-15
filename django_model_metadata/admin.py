from django.contrib import admin
from .models import ModelGeneralMetaData
from .forms import GeneralMetadataForm


@admin.register(ModelGeneralMetaData)
class ModelGeneralMetaDataAdmin(admin.ModelAdmin):
    list_display = ("name", "field_name", "meta_type", "searchable", "widget_attrs", "created_at", "id")
    list_filter = (
        "created_at",
        "searchable",
    )
    search_fields = ("name",)
    prepopulated_fields = {"field_name": ["name"]}
    form = GeneralMetadataForm
