from django.contrib import admin
from .models import ModelGeneralMetaData

@admin.register(ModelGeneralMetaData)
class ModelGeneralMetaDataAdmin(admin.ModelAdmin):
    list_display = ('name', 'meta_type', 'searchable')
    search_fields = ('name', 'field_name')
    list_filter = ('meta_type', 'searchable')