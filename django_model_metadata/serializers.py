from rest_framework import serializers
from .models import ModelGeneralMetaData

class GeneralMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelGeneralMetaData
        fields = ["id", "name", "field_name", "meta_type"]


class GeneralMetadataListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelGeneralMetaData
        fields = ["id", "name", "field_name", "meta_type", "widget_attrs"]