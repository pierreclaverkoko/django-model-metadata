from django.db import models
import swapper
from .model_mixins import GeneralMetadataMixin


class ModelGeneralMetaData(GeneralMetadataMixin):
    """
    Metadata model
    For general use
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        swappable = swapper.swappable_setting("django_model_metadata", "ModelGeneralMetaData")
