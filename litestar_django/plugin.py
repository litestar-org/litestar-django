from typing import Any

from django.db import models  # type: ignore[import-untyped]
from litestar.plugins.base import SerializationPlugin
from litestar.typing import FieldDefinition

from litestar_django.dto import DjangoModelDTO


class DjangoModelPlugin(SerializationPlugin):
    def __init__(self) -> None:
        self._type_dto_map: dict[type[models.Model], type[DjangoModelDTO[Any]]] = {}

    def supports_type(self, field_definition: FieldDefinition) -> bool:
        return (
            field_definition.is_collection
            and field_definition.has_inner_subclass_of(models.Model)
        ) or field_definition.is_subclass_of(models.Model)

    def create_dto_for_type(
        self, field_definition: FieldDefinition
    ) -> type[DjangoModelDTO[Any]]:
        # assumes that the type is a container of Django models or a single Django model
        annotation = next(
            (
                inner_type.annotation
                for inner_type in field_definition.inner_types
                if inner_type.is_subclass_of(models.Model)
            ),
            field_definition.annotation,
        )
        if annotation in self._type_dto_map:
            return self._type_dto_map[annotation]

        self._type_dto_map[annotation] = dto_type = DjangoModelDTO[annotation]  # type:ignore[valid-type]

        return dto_type
