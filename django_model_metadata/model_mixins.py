import logging

from django import forms
from django.apps import apps
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import JSONField
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.contrib.humanize.templatetags.humanize import intcomma
import swapper

logger = logging.getLogger(__name__)


class GeneralMetadataMixin(models.Model):
    """
    Metadata mixin class for defining elements
    """

    CHARFIELD = "CharField"
    DECIMALFIELD = "DecimalField"
    INTEGERFIELD = "IntegerField"
    DATEFIELD = "DateField"
    DATETIMEFIELD = "DateTimeField"
    FK = "ForeignKey"
    JSON = "JSONField"
    CHOICEFIELD = "ChoiceField"
    METADATA_TYPE_CHOICES = (
        (CHARFIELD, _("Text")),
        (DATEFIELD, _("Date")),
        (DATETIMEFIELD, _("DateTime")),
        (INTEGERFIELD, _("Integer")),
        (DECIMALFIELD, _("Decimal Number")),
        (FK, _("Relation")),
        (JSON, _("JSON Data")),
        (CHOICEFIELD, _("Normal Select")),
    )
    name = models.CharField(max_length=200, verbose_name=_("Metadata name"))
    field_name = models.CharField(
        max_length=200,
        verbose_name=_("Metadata field name"),
        null=True,
        blank=True,
        help_text=_("Spaces and '-' will be replaced by '_'"),
    )
    meta_type = models.CharField(max_length=20, choices=METADATA_TYPE_CHOICES, verbose_name=_("Metadata type"))
    searchable = models.BooleanField(default=False, verbose_name=_("Searchable ?"))
    widget_attrs = JSONField(blank=True, verbose_name=_("Attributes (JSON Format)"))

    class Meta:
        app_label = "config"
        verbose_name = _("Elements Metadata")
        verbose_name_plural = _("Elements Metadatas")
        abstract = True

    def __str__(self):
        return f"{self.name} ({self.meta_type})"

    def clean(self):
        if not self.widget_attrs:
            self.widget_attrs = {}

        # Defining defaults
        self.populate_default_attrs()

        attrs_form = self.get_attrs_form_class()(self.widget_attrs)
        if not attrs_form.is_valid():
            logger.error(f"Error in metadata form : {attrs_form.errors}")
            raise ValidationError({"widget_attrs": attrs_form.errors})

        # replace '-' and ' ' with '_' in field_name
        if not self.field_name:
            self.field_name = slugify(self.name)

        self.field_name = self.field_name.strip().replace("-", "_").replace(" ", "_")

    def get_form_field_object(self, initial=None):
        field_attrs = self.widget_attrs

        if self.meta_type == self.FK:
            model_class = self.get_metadata_model()
            field_attrs.pop("on_delete", None)
            field_attrs.pop("model", None)
            if model_class:
                field_attrs["queryset"] = model_class.objects.all()
            else:
                field_attrs["queryset"] = self.__class__.objects.none()
        elif self.meta_type == self.CHOICEFIELD:
            field_attrs.pop("values", None)
        field = GENERAL_FIELDS_MAP[self.meta_type](**field_attrs, label=self.name, initial=initial)

        return field

    def get_form_field_name(self):
        if not self.field_name:
            name = slugify(self.name)
            self.field_name = "_".join(name.split("-"))
            self.save()
        return self.field_name

    def get_form_field(self, form):
        field = self.get_form_field_object()
        field_name = self.get_form_field_name()
        if field:
            return field.get_bound_field(form, field_name)

    def get_field_schema(self):
        return {"type": GENERAL_JSON_FORM_FIELDS_MAP[self.meta_type], "title": self.name}

    def populate_default_attrs(self, commit=False):
        # We reinitialize the attributes if they don't match the object
        if self.meta_type == self.CHARFIELD and (not "max_length" in self.widget_attrs):
            self.widget_attrs = {"max_length": 255}

        elif self.meta_type == self.DECIMALFIELD:
            self.widget_attrs = {}
            if not "max_digits" in self.widget_attrs:
                self.widget_attrs["max_digits"] = 30
            if not "decimal_places" in self.widget_attrs:
                self.widget_attrs["decimal_places"] = 2

        # Remove these attrs
        if self.meta_type == self.CHARFIELD:
            self.widget_attrs.pop("max_digits", None)
            self.widget_attrs.pop("decimal_places", None)
        elif self.meta_type == self.DECIMALFIELD:
            self.widget_attrs.pop("max_length", None)
        else:
            self.widget_attrs.pop("max_length", None)
            self.widget_attrs.pop("max_digits", None)
            self.widget_attrs.pop("decimal_places", None)
            self.widget_attrs.pop("on_delete", None)

        if commit:
            self.save()

    def get_metadata_model(self):
        if self.meta_type == self.FK:
            model_name = self.widget_attrs.get("model", None)
            if model_name:
                try:
                    ModelClass = apps.get_model(model_name)
                    return ModelClass
                except Exception:
                    ...

    def get_attrs_form(self):
        if self.widget_attrs:
            self.populate_default_attrs(commit=True)
            return self.get_attrs_form_class()(self.widget_attrs)
        else:
            return self.get_attrs_form_class()()

    def get_attrs_form_class(self):
        fields_list = GENERAL_FIELDS_DEFAULT_ATTRS[self.meta_type]

        class AttrsForm(forms.Form):
            """
            The document metadata attrs form to fill dynamically with fields
            """

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

                for attr in fields_list:
                    self.fields[attr[0]] = attr[1]

        return AttrsForm

    def get_widget_attrs_schema(self):
        schema = {"type": "dict", "keys": {}}
        fields_list = GENERAL_FIELDS_DEFAULT_ATTRS[self.meta_type]
        for attr in fields_list:
            attr_json_data = {"type": attr[2], "title": attr[1].label}

            # Do stuff here if any
            if self.meta_type == self.FK:
                if attr[0] == "model":
                    attr_json_data["widget"] = "autocomplete"
                    attr_json_data["handler"] = reverse("metadata-autocomplete", kwargs={"el_type": "models"})
                elif attr[0] == "on_delete":
                    attr_json_data["widget"] = "autocomplete"
                    attr_json_data["handler"] = reverse("metadata-autocomplete", kwargs={"el_type": "on_delete"})

            schema["keys"][attr[0]] = attr_json_data

        schema["additionalProperties"] = {"type": "string"}

        return schema


GENERAL_FK_MODELS = (
    ("market.Market", _("Market")),
    ("market.Product", _("Product")),
    ("main.PtProvince", _("Province")),
)
OLD_ON_DELETE_CHOICES = (
    (models.CASCADE, _("Cascade")),
    (models.DO_NOTHING, _("Do Nothing")),
    (models.SET_NULL, _("Set Null")),
    (models.PROTECT, _("Protect")),
)
ON_DELETE_CHOICES = (
    ("CASCADE", _("Cascade")),
    ("DO_NOTHING", _("Do Nothing")),
    ("SET_NULL", _("Set Null")),
    ("PROTECT", _("Protect")),
)


GENERAL_FIELDS_MAP = {
    GeneralMetadataMixin.CHARFIELD: forms.CharField,
    GeneralMetadataMixin.DECIMALFIELD: forms.DecimalField,
    GeneralMetadataMixin.DATEFIELD: forms.DateField,
    GeneralMetadataMixin.DATETIMEFIELD: forms.DateTimeField,
    GeneralMetadataMixin.INTEGERFIELD: forms.IntegerField,
    GeneralMetadataMixin.FK: forms.ModelChoiceField,
    GeneralMetadataMixin.JSON: JSONField,
    GeneralMetadataMixin.CHOICEFIELD: forms.ChoiceField,
}

GENERAL_FRONTEND_FIELDS_MAP = {
    GeneralMetadataMixin.CHARFIELD: "text",
    GeneralMetadataMixin.DECIMALFIELD: "text",
    GeneralMetadataMixin.DATEFIELD: "date",
    GeneralMetadataMixin.DATETIMEFIELD: "datetime",
    GeneralMetadataMixin.INTEGERFIELD: "number",
    GeneralMetadataMixin.FK: "select",
    GeneralMetadataMixin.JSON: "text",
    GeneralMetadataMixin.CHOICEFIELD: "select",
}

GENERAL_JSON_FORM_FIELDS_MAP = {
    GeneralMetadataMixin.CHARFIELD: "string",
    GeneralMetadataMixin.DECIMALFIELD: "string",
    GeneralMetadataMixin.DATEFIELD: "string",
    GeneralMetadataMixin.DATETIMEFIELD: "string",
    GeneralMetadataMixin.INTEGERFIELD: "number",
    GeneralMetadataMixin.FK: "integer",
    GeneralMetadataMixin.JSON: "string",
    GeneralMetadataMixin.CHOICEFIELD: "list",
}


GENERAL_FIELDS_DEFAULT_ATTRS = {
    GeneralMetadataMixin.CHARFIELD: [("max_length", forms.IntegerField(label=_("Max length")), "number")],
    GeneralMetadataMixin.DECIMALFIELD: [
        ("max_digits", forms.IntegerField(label=_("Max digits")), "number"),
        ("decimal_places", forms.IntegerField(label=_("Decimal places")), "number"),
    ],
    GeneralMetadataMixin.DATEFIELD: [],
    GeneralMetadataMixin.DATETIMEFIELD: [],
    GeneralMetadataMixin.INTEGERFIELD: [],
    GeneralMetadataMixin.FK: [
        (
            "model",
            forms.ChoiceField(choices=GENERAL_FK_MODELS, label=_("Relation"), required=False),
            "string",
        ),
        (
            "on_delete",
            forms.ChoiceField(choices=ON_DELETE_CHOICES, label=_("Action on delete"), required=False),
            "string",
        ),
    ],
    GeneralMetadataMixin.JSON: [],
    GeneralMetadataMixin.CHOICEFIELD: [],
}


class GeneralMetadataTypeMixin(models.Model):
    """
    The metadata type model that contains the links to metadata definitions
    """

    metadata = models.ManyToManyField(
        swapper.get_model_name("django_model_metadata", "ModelGeneralMetaData"), blank=True, verbose_name=_("Metadata")
    )

    class Meta:
        abstract = True

    def get_form_class(self, metadata_field_name=None):
        if not metadata_field_name:
            metadata_field_name = "metadata"

        metadata_field = getattr(self, metadata_field_name, "metadata")
        metadata_ = metadata_field.all()

        class GeneralTypeForm(forms.Form):
            """
            The General type form to fill dynamically with fields
            """

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

                for data in metadata_:
                    self.fields[data.get_form_field_name()] = data.get_form_field_object()

        return GeneralTypeForm

    def get_fields_schema(self, metadata_field_name=None):
        if not metadata_field_name:
            metadata_field_name = "metadata"

        metadata_field = getattr(self, metadata_field_name, "metadata")
        metadata_ = metadata_field.all()

        schema = {"type": "dict", "keys": {}}
        schema_fields = {}

        for data in metadata_:
            schema_fields[data.get_form_field_name()] = data.get_field_schema()

        schema["keys"] = schema_fields

        return schema

    def get_form(self):
        return self.get_form_class()()


class CustomMetadataMixin(models.Model):
    """
    The model mixin that adds the element json data to a model.
    Those json data are validated through the metadata type model using metadata data.
    """

    element_metadata = models.JSONField(null=True, blank=True)

    class Meta:
        abstract = True

    def get_element_type(self):
        raise NotImplementedError(
            f"Every child to '{self.__class__}' must implement this function to return the element type"
        )

    def get_formatted_metadata(self, get_string=False):
        element_metadata = self.element_metadata

        # If there is no metadata, we return None to avoid further executions
        if not element_metadata:
            return None

        # FORMATTING RELATION METADATA
        element_type = self.get_element_type()
        element_fks = element_type.metadata.filter(meta_type=GeneralMetadataMixin.FK)
        if element_fks.exists():
            for element_fk in element_fks:
                element_fk_model = element_fk.get_metadata_model()
                if element_fk_model:
                    try:
                        element_fk_instance = element_fk_model.objects.get(
                            id=element_metadata.get(element_fk.field_name, None)
                        )
                        if get_string:
                            # If the model has the function 'get_metadata_description'
                            # we use it to show description
                            # else we use the '__str__' function
                            elemt_fk_str_function = getattr(
                                element_fk_instance, f"get_metadata_description", element_fk_instance.__str__
                            )
                            element_metadata[element_fk.field_name] = elemt_fk_str_function()
                        else:
                            element_metadata[element_fk.field_name] = element_fk_instance
                    except element_fk_model.DoesNotExist:
                        pass

        # FORMATTING DECIMAL AND INTEGER METADATA
        element_numbers = element_type.metadata.filter(
            meta_type__in=[GeneralMetadataMixin.INTEGERFIELD, GeneralMetadataMixin.DECIMALFIELD]
        )
        if element_numbers.exists():
            for element_number in element_numbers:
                number_value = element_metadata.get(element_number.field_name, None)
                if number_value:
                    element_metadata[element_number.field_name] = intcomma(number_value)

        return element_metadata

    def get_metadata_form_class(self):
        elmt_type = self.get_element_type()
        if elmt_type:
            return elmt_type.get_form_class()

    def get_metadata_form(self):
        if self.element_metadata:
            return self.get_metadata_form_class()(self.element_metadata)
        else:
            return self.get_metadata_form_class()

    def clean(self):
        # Converting Models to PK
        if self.element_metadata:
            for k, v in self.element_metadata.items():
                try:
                    self.element_metadata[k] = v.pk
                except BaseException:
                    pass

        # Cleaning the element type
        # element_type = self.get_element_type()
        # if not isinstance(getattr(element_type, "metadata", None), GeneralMetaData):
        #     raise ValidationError(_("The element type linked to this metadata is incomplete"))

        metadata_form = self.get_metadata_form()
        if not metadata_form:
            logger.debug("No metadata form implemented")
            return None

        try:
            if not metadata_form.is_valid():
                logger.error(f"GOT ERROR FOR METADATA FORM : ${metadata_form.errors.as_json()}")
                raise ValidationError({"element_metadata": metadata_form.errors.as_json()})
        except TypeError as e:
            logger.error(f"Metadata form error : {e}")
