django-model-metadata
=====================

django-model-metadata is a Django app to add metadata logics to django models.

Quick start
-----------

1. Add "polls" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...,
        "django_model_metadata",
        "django_jsonform",
    ]

2. Include the polls URLconf in your project urls.py like this::

    path("metadata/", include("django_model_metadata.urls")),

3. Run ``python manage.py migrate`` to create the models.

4. Start the development server and visit the admin to create a poll.

Usage
-----

First of all, you can use the ``django_model_metadata.models.ModelGeneralMetaData`` globally to add metadata to any model.
If you do not want to use this model, you can create your own model and inherit from ``django_model_metadata.models.ModelGeneralMetaData``.
This will save all the metadata needed by all the other models.

Considering you have a procurement application. You create a ``Material`` model and want to have different attributes for each material type.
The ``Material`` model must inherit the ``django_model_metadata.model_mixins.CustomMetadataMixin`` class and define the function ``get_element_type`` to mention the field that represents the type model that defines the metadata.

The ``MaterialType`` model will define the metadata.
Then when we save the ``Material`` instance, a form will be automatically created to validate the data sent in ``element_metadata`` field, according to the metadata definition in ``MaterialType``.

You will then have the following :

.. code-block:: python

    from django.db import models
    from django_model_metadata import GeneralMetadataTypeMixin, CustomMetadataMixin

    class MaterialType(GeneralMetadataTypeMixin):
        name = models.CharField(max_length=255)
        description = models.TextField(blank=True, null=True)

        class Meta:
            verbose_name = "Material Type"
            verbose_name_plural = "Material Types"

    class Material(CustomMetadataMixin):
        name = models.CharField(max_length=255)
        description = models.TextField(blank=True, null=True)
        material_type = models.ForeignKey("MaterialType", on_delete=models.CASCADE, related_name="materials")

        def get_element_type(self):
            return self.material_type

You can then use the admin interface to add metadata into ``ModelGeneralMetaData``, or your choosen model.
