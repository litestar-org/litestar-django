import dataclasses
import datetime
import decimal
import uuid
from typing import (
    TypeVar,
    Generic,
    Type,
    Any,
    Generator,
    List,
    Optional,
    Callable,
    Mapping,
)

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

try:
    from enumfields import EnumField  # type: ignore[import-untyped]
except ImportError:
    EnumField = None


def _get_model_attribute(obj: Model, attr: str) -> Any:
    value = getattr(obj, attr)
    if isinstance(value, Manager):
        value = list(value.all())
    return value


@dataclasses.dataclass(frozen=True)
class DjangoDTOConfig(DTOConfig):
    ignore_inverse_match_regex_validators: bool = False
    """
    When setting 'inverse_match=True' on a RegexValidator, ignore the validator instead
    of raising en exception
    """


class DjangoModelDTO(AbstractDTO[T], Generic[T]):
    attribute_accessor = _get_model_attribute
    custom_field_types: Optional[dict[type[AnyField], Any]] = None

    @classmethod
    def get_field_type(cls, field: Field, type_map: dict[type[AnyField], Any]) -> Any:
        if EnumField is not None and isinstance(field, EnumField):
            return field.enum

        for field_cls, type_ in type_map.items():
            if isinstance(field, field_cls):
                return type_

        return Any

    @classmethod
    def get_field_constraints(cls, field: AnyField) -> KwargDefinition:
        constraints = {}
        if isinstance(field, Field):
            constraints["title"] = (
                str(field.verbose_name) if field.verbose_name else field.name
            )  # might be a proxy

            if field.help_text:
                constraints["description"] = field.help_text

            # add choices as enum. if field is an enum type, we hand this off to
            # Litestar for native enum support
            if field.choices and not (EnumField and isinstance(field, EnumField)):
                choices = field.choices
                if isinstance(choices, Mapping):
                    constraints["enum"] = list(choices.keys())
                else:
                    constraints["enum"] = [c[0] for c in choices]

            for validator in field.validators:
                # fast path for known supported validators
                # nullable fields do not support these constraints and for enum the
                # constraint is defined implicitly by its values
                if not field.null and "enum" not in constraints:
                    if isinstance(validator, validators.MinValueValidator):
                        constraints["gt"] = validator.limit_value
                    elif isinstance(validator, validators.MinLengthValidator):
                        constraints["min_length"] = validator.limit_value
                    elif isinstance(validator, validators.MaxValueValidator):
                        constraints["lt"] = validator.limit_value
                    elif isinstance(validator, validators.MaxLengthValidator):
                        constraints["max_length"] = validator.limit_value
                if isinstance(validator, validators.RegexValidator):
                    if validator.inverse_match:
                        if (
                            isinstance(cls.config, DjangoDTOConfig)
                            and cls.config.ignore_inverse_match_regex_validators
                        ):
                            continue
                        else:
                            raise ValueError(
                                f"RegexValidator(regex='{validator.regex}') with "
                                "'inverse_match=True' cannot be presented as a pattern "
                                "in OpenAPI. Construct the pattern in a way that only a"
                                "valid string matches, or set "
                                "DjangoDTOConfig(ignore_inverse_match_regex_validators=True), "
                                "to skip setting the 'pattern' property in the OpenAPI "
                                "schema"
                            )
                    constraints["pattern"] = validator.regex.pattern

                else:
                    # handle generic validators
                    constraints.update(cls.create_constraints_for_validator(validator))

        else:
            constraints["title"] = field.name

        return KwargDefinition(**constraints)  # type: ignore[arg-type]

    @classmethod
    def create_constraints_for_validator(
        cls, validator: Callable[[Any], None]
    ) -> dict[str, Any]:
        """
        Create constraints for field validators. Must return a dictionary that can be
        passed to 'KwargDefinition'
        """
        return {}

    @classmethod
    def get_field_default(
        cls, field: AnyField
    ) -> tuple[Any, Optional[Callable[..., Any]]]:
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
