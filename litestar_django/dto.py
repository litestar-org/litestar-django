import datetime
import decimal
import uuid
from typing import TypeVar, Generic, Type, Any, Generator, List, Optional, Callable

from django.core import validators  # type: ignore[import-untyped]
from django.db import models  # type: ignore[import-untyped]
from django.db.models import (  # type: ignore[import-untyped]
    Model,
    ForeignKey,
    OneToOneField,
    ManyToManyField,
    Field,
    ManyToOneRel,
    Manager,
    ForeignObjectRel,
)
from django.db.models.fields import NOT_PROVIDED  # type: ignore[import-untyped]
from litestar.connection import ASGIConnection
from litestar.dto import DTOField
from litestar.dto.base_dto import AbstractDTO
from litestar.dto.config import DTOConfig
from litestar.dto.data_structures import DTOFieldDefinition
from litestar.params import KwargDefinition
from litestar.types import Empty
from litestar.typing import FieldDefinition

from litestar_django.types import AnyField

T = TypeVar("T", bound=Model)


_FIELD_TYPE_MAP: dict[type[Field], Any] = {
    # complex types come first so they won't be overwritten by their superclasses
    models.JSONField: Any,
    models.DecimalField: decimal.Decimal,
    models.DateTimeField: datetime.datetime,
    models.DateField: datetime.date,
    models.TimeField: datetime.time,
    models.DurationField: datetime.timedelta,
    models.FileField: str,
    models.FilePathField: str,
    models.UUIDField: uuid.UUID,
    models.IntegerField: int,
    models.FloatField: float,
    models.BooleanField: bool,
    models.CharField: str,
    models.TextField: str,
    models.BinaryField: bytes,
}


def _get_model_attribute(obj: Model, attr: str) -> Any:
    value = getattr(obj, attr)
    if isinstance(value, Manager):
        value = list(value.all())
    return value


class DjangoModelDTO(AbstractDTO[T], Generic[T]):
    attribute_accessor = _get_model_attribute
    custom_field_types: dict[type[AnyField], Any] | None = None

    @classmethod
    def get_config_for_model_type(
        cls, config: DTOConfig, model_type: Type[T]
    ) -> DTOConfig:
        return config

    @classmethod
    def get_field_type(cls, field: Field, type_map: dict[type[AnyField], Any]) -> Any:
        for field_cls, type_ in type_map.items():
            if isinstance(field, field_cls):
                return type_
        return Any

    @classmethod
    def get_field_constraints(cls, field: AnyField) -> KwargDefinition:
        constraints = {}
        if isinstance(field, Field):
            constraints["title"] = field.verbose_name

            if field.help_text:
                constraints["description"] = field.help_text

            for validator in field.validators:
                if isinstance(
                    validator,
                    (validators.MinLengthValidator, validators.MinValueValidator),
                ):
                    constraints["gt"] = validator.limit_value
                elif isinstance(
                    validator,
                    (validators.MaxLengthValidator, validators.MaxValueValidator),
                ):
                    constraints["lt"] = validator.limit_value

        else:
            constraints["title"] = field.name

        return KwargDefinition(**constraints)

    @classmethod
    def get_field_default(
        cls, field: AnyField
    ) -> tuple[Any, Callable[..., Any] | None]:
        if isinstance(field, ForeignObjectRel):
            if isinstance(field, ManyToOneRel):
                return Empty, list
            return Empty, None

        if isinstance(field, ManyToManyField):
            return Empty, list

        default = field.default
        default_factory = None
        if default is NOT_PROVIDED:
            default = Empty
        elif callable(default):
            default_factory = default
            default = Empty

        return default, default_factory

    @classmethod
    def generate_field_definitions(
        cls, model_type: Type[T]
    ) -> Generator[DTOFieldDefinition, None, None]:
        field_type_map = _FIELD_TYPE_MAP
        if cls.custom_field_types:
            field_type_map = {**_FIELD_TYPE_MAP, **cls.custom_field_types}

        field: AnyField
        for field in model_type._meta.get_fields():
            name = field.name

            if field.hidden:
                dto_field = DTOField("private")
            elif not field.editable:
                dto_field = DTOField("read-only")
            else:
                dto_field = DTOField()

            if field.is_relation and field.related_model:
                related = field.related_model
                if isinstance(field, (ForeignKey, OneToOneField)):
                    field_type: Any = related
                elif isinstance(field, ManyToManyField) or getattr(
                    field, "one_to_many", False
                ):
                    field_type = List[related]  # type: ignore[valid-type]
                else:
                    field_type = Any

            else:
                field_type = cls.get_field_type(field, type_map=field_type_map)

            if field.null and not isinstance(field, ManyToOneRel):
                # 'ManyToOneRel's are nullable from Django's perspective, but we add a
                # 'list' default factory, so we know they can never actually be 'None'
                field_type = Optional[field_type]

            default, default_factory = cls.get_field_default(field)

            field_definition = FieldDefinition.from_annotation(
                annotation=field_type,
                name=name,
                default=default,
                kwarg_definition=cls.get_field_constraints(field),
            )

            yield DTOFieldDefinition.from_field_definition(
                field_definition,
                model_name=model_type.__name__,
                default_factory=default_factory,
                dto_field=dto_field,
            )

    @classmethod
    def detect_nested_field(cls, field_definition: FieldDefinition) -> bool:
        """
        Leverage DTOFieldDefinition.is_subclass_of to detect nested Models or sequences of Models.
        """
        return field_definition.is_subclass_of(Model)
