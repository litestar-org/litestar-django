import contextlib
from typing import Any

from django.db import models  # type: ignore[import-untyped]
from litestar.config.app import AppConfig
from litestar.plugins.base import SerializationPlugin, InitPlugin
from litestar.typing import FieldDefinition

from litestar_django.dto import DjangoModelDTO


class DjangoModelPlugin(InitPlugin, SerializationPlugin):
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

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        type_encoders = (
            dict(app_config.type_encoders) if app_config.type_encoders else {}
        )
        type_decoders = (
            list(app_config.type_decoders) if app_config.type_decoders else []
        )
        with contextlib.suppress(ImportError):
            import enumfields  # type: ignore[import-untyped]

            def _is_enumfields_enum(v: Any) -> bool:
                return issubclass(v, (enumfields.Enum, enumfields.IntEnum))

            def _decode_enumfields_enum(type_: Any, value: Any) -> Any:
                return type_(value)

            type_encoders[enumfields.Enum] = lambda v: v.value
            type_encoders[enumfields.IntEnum] = lambda v: v.value

            type_decoders.append((_is_enumfields_enum, _decode_enumfields_enum))

        app_config.type_encoders = type_encoders
        app_config.type_decoders = type_decoders

        return app_config
