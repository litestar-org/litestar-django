from django.contrib.contenttypes.fields import GenericForeignKey  # type: ignore[import-untyped]
from django.db.models import Field, ForeignObjectRel  # type: ignore[import-untyped]

AnyField = Field | ForeignObjectRel | GenericForeignKey
