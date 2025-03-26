from rest_framework import serializers
from .models import GeneralMetaData

class GeneralMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralMetaData
        fields = ["id", "name", "field_name", "meta_type"]


class GeneralMetadataListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralMetaData
        fields = ["id", "name", "field_name", "meta_type", "widget_attrs"]