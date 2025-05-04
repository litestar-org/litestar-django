from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import TypeAlias
    from django.contrib.contenttypes.fields import GenericForeignKey  # type: ignore[import-untyped]
    from django.db.models import Field, ForeignObjectRel  # type: ignore[import-untyped]

AnyField: TypeAlias = "Field | ForeignObjectRel | GenericForeignKey"
