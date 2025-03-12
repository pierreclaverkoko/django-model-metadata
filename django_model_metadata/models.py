from .model_mixins import GeneralMetadataMixin
import swapper


class ModelGeneralMetaData(GeneralMetadataMixin):
    """
    Metadata model
    For general use
    """

    class Meta:
        swappable = swapper.swappable_setting("django_model_metadata", "ModelGeneralMetaData")
