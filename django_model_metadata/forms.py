import logging
from django import forms
from django_jsonform.widgets import JSONFormWidget


logger = logging.getLogger(__name__)


class MetadataFormMixin:
    _metadata_field = "element_metadata"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self._metadata_field:
            self._metadata_field = "element_metadata"

        try:
            elmt_type = self.instance.get_element_type()
        except Exception as e:  # TODO : except relation model does not exist
            print("BUG FORM METADATA ::: ", e)
            elmt_type = None

        if elmt_type:
            self.fields[self._metadata_field].widget = JSONFormWidget(schema=elmt_type.get_fields_schema())


class JsonElementFormMixin:
    _metadata_field = "element_metadata"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self._metadata_field:
            self._metadata_field = "element_metadata"

        try:
            func_ = getattr(self.instance, f"get_{self._metadata_field}_schema", None)
            if func_:
                element_schema = func_()
            else:
                element_schema = None
        except Exception as e:
            print("BUG JSON METADATA ::: ", e)
            element_schema = None

        if element_schema:
            self.fields[self._metadata_field].widget = JSONFormWidget(schema=element_schema)


class GeneralMetadataForm(JsonElementFormMixin, forms.ModelForm):
    _metadata_field = "widget_attrs"
