import datetime
import decimal
import uuid
from typing import Optional, List, Any, Annotated

import pytest
from litestar.dto import DTOFieldDefinition, DTOField
from litestar.params import KwargDefinition
from litestar.typing import FieldDefinition
import django


from litestar_django.dto import DjangoModelDTO, DjangoDTOConfig
from tests.some_app.app.models import (
    Author,
    ModelWithFields,
    make_default,
    Book,
    Genre,
    MyStringField,
    StdEnum,
    LabelledEnum,
    ModelInvalidRegexValidator,
)

# django extract these from SQLite on 5.1 and above
if django.get_version().startswith("5"):
    MAX_INT_VALUE = 9223372036854775807
    MIN_INT_VALUE = -9223372036854775808
else:
    MAX_INT_VALUE = None
    MIN_INT_VALUE = None


def test_basic_field_types() -> None:
    dto_type = DjangoModelDTO[ModelWithFields]
    field_defs = {
        f.name: f for f in dto_type.generate_field_definitions(ModelWithFields)
    }

    assert field_defs["id"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            int,
            name="id",
            kwarg_definition=KwargDefinition(
                title="ID",
                lt=MAX_INT_VALUE,  # max int value set by django
                gt=MIN_INT_VALUE,  # min int value set by django
            ),
        ),
    )

    assert field_defs["json_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            Any,
            name="json_field",
            kwarg_definition=KwargDefinition(
                title="json field",
            ),
        ),
    )

    assert field_defs["decimal_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            decimal.Decimal,
            name="decimal_field",
            kwarg_definition=KwargDefinition(
                title="decimal field",
            ),
        ),
    )

    assert field_defs["datetime_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            datetime.datetime,
            name="datetime_field",
            kwarg_definition=KwargDefinition(
                title="datetime field",
            ),
        ),
    )

    assert field_defs["date_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            datetime.date,
            name="date_field",
            kwarg_definition=KwargDefinition(
                title="date field",
            ),
        ),
    )

    assert field_defs["time_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            datetime.time,
            name="time_field",
            kwarg_definition=KwargDefinition(
                title="time field",
            ),
        ),
    )

    assert field_defs["duration_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            datetime.timedelta,
            name="duration_field",
            kwarg_definition=KwargDefinition(
                title="duration field",
            ),
        ),
    )

    assert field_defs["file_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            str,  # files render as their path, so 'str'
            name="file_field",
            kwarg_definition=KwargDefinition(
                title="file field",
            ),
        ),
    )

    assert field_defs["file_path_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            str,
            name="file_path_field",
            kwarg_definition=KwargDefinition(
                title="file path field",
            ),
        ),
    )

    assert field_defs["uuid_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            uuid.UUID,
            name="uuid_field",
            kwarg_definition=KwargDefinition(
                title="uuid field",
            ),
        ),
    )

    assert field_defs["integer_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            int,
            name="integer_field",
            kwarg_definition=KwargDefinition(
                title="integer field",
                # min/max int values set by django, obtained from the DB (sqlite in our case)
                lt=MAX_INT_VALUE,
                gt=MIN_INT_VALUE,
            ),
        ),
    )

    assert field_defs["float_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            float,
            name="float_field",
            kwarg_definition=KwargDefinition(
                title="float field",
            ),
        ),
    )

    assert field_defs["bool_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            bool,
            name="bool_field",
            kwarg_definition=KwargDefinition(
                title="bool field",
            ),
        ),
    )

    assert field_defs["char_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            str,
            name="char_field",
            kwarg_definition=KwargDefinition(
                title="char field",
                max_length=100,
            ),
        ),
    )

    assert field_defs["text_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            str,
            name="text_field",
            kwarg_definition=KwargDefinition(
                title="text field",
            ),
        ),
    )

    assert field_defs["binary_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            bytes,
            name="binary_field",
            kwarg_definition=KwargDefinition(
                title="binary field",
            ),
        ),
    )

    assert field_defs["enum_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            StdEnum,
            name="enum_field",
            kwarg_definition=KwargDefinition(
                title="enum field",
            ),
        ),
    )

    assert field_defs[
        "labelled_enum_field"
    ] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            LabelledEnum,
            name="labelled_enum_field",
            kwarg_definition=KwargDefinition(
                title="labelled enum field",
            ),
        ),
    )

    assert field_defs["field_with_choices"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            str,
            name="field_with_choices",
            kwarg_definition=KwargDefinition(
                title="field with choices",
                enum=["foo", "bar"],
            ),
        ),
    )

    assert field_defs[
        "field_with_regex_validator"
    ] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            str,
            name="field_with_regex_validator",
            kwarg_definition=KwargDefinition(
                title="field with regex validator",
                pattern=r"\d{3}",
                max_length=100,
            ),
        ),
    )

    assert field_defs[
        "field_with_non_string_verbose_name"
    ] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            str,
            name="field_with_non_string_verbose_name",
            kwarg_definition=KwargDefinition(
                title="Some field",
                max_length=100,
            ),
        ),
    )


def test_invalid_regex_validator() -> None:
    dto_type = DjangoModelDTO[ModelInvalidRegexValidator]
    with pytest.raises(ValueError, match="inverse_match=True"):
        tuple(dto_type.generate_field_definitions(ModelInvalidRegexValidator))

    dto_type = DjangoModelDTO[
        Annotated[
            ModelInvalidRegexValidator,
            DjangoDTOConfig(ignore_inverse_match_regex_validators=True),
        ]
    ]
    definitions = {
        f.name: f
        for f in dto_type.generate_field_definitions(ModelInvalidRegexValidator)
    }
    assert not definitions["invalid_regex_validator"].kwarg_definition.pattern


def test_constraints() -> None:
    dto_type = DjangoModelDTO[ModelWithFields]
    field_defs = {
        f.name: f for f in dto_type.generate_field_definitions(ModelWithFields)
    }

    assert field_defs["min_1_int_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            int,
            name="min_1_int_field",
            kwarg_definition=KwargDefinition(
                title="min 1 int field",
                gt=1,
                lt=MAX_INT_VALUE,  # max int value set by django
            ),
        ),
    )

    assert field_defs[
        "min_2_max_5_int_field"
    ] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            int,
            name="min_2_max_5_int_field",
            kwarg_definition=KwargDefinition(
                title="min 2 max 5 int field",
                gt=2,
                lt=5,
            ),
        ),
    )

    assert field_defs["min_1_str_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            str,
            name="min_1_str_field",
            kwarg_definition=KwargDefinition(
                title="min 1 str field",
                min_length=1,
                max_length=100,
            ),
        ),
    )


def test_nullable_field() -> None:
    dto_type = DjangoModelDTO[ModelWithFields]
    field_defs = {
        f.name: f for f in dto_type.generate_field_definitions(ModelWithFields)
    }

    assert field_defs["nullable_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            Optional[str],
            name="nullable_field",
            kwarg_definition=KwargDefinition(
                title="nullable field",
            ),
        ),
    )


def test_default() -> None:
    dto_type = DjangoModelDTO[ModelWithFields]
    field_defs = {
        f.name: f for f in dto_type.generate_field_definitions(ModelWithFields)
    }

    assert field_defs["field_with_default"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            Optional[str],
            name="field_with_default",
            default="hello",
            kwarg_definition=KwargDefinition(
                title="field with default",
            ),
        ),
    )

    assert field_defs[
        "field_with_default_callable"
    ] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=make_default,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            Optional[str],
            name="field_with_default_callable",
            kwarg_definition=KwargDefinition(
                title="field with default callable",
            ),
        ),
    )


def test_description_from_help_text() -> None:
    dto_type = DjangoModelDTO[ModelWithFields]
    field_defs = {
        f.name: f for f in dto_type.generate_field_definitions(ModelWithFields)
    }

    assert field_defs[
        "field_with_help_text"
    ] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            str,
            name="field_with_help_text",
            kwarg_definition=KwargDefinition(
                title="field with help text",
                description="This is a help text",
                max_length=100,
            ),
        ),
    )


def test_title_from_verbose_name() -> None:
    dto_type = DjangoModelDTO[ModelWithFields]
    field_defs = {
        f.name: f for f in dto_type.generate_field_definitions(ModelWithFields)
    }

    assert field_defs["renamed_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            str,
            name="renamed_field",
            kwarg_definition=KwargDefinition(
                title="That's not my name", max_length=100
            ),
        ),
    )


def test_non_editable_field() -> None:
    dto_type = DjangoModelDTO[ModelWithFields]
    field_defs = {
        f.name: f for f in dto_type.generate_field_definitions(ModelWithFields)
    }

    assert field_defs["non_editable_field"] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField("read-only"),
        field_definition=FieldDefinition.from_annotation(
            str,
            name="non_editable_field",
            kwarg_definition=KwargDefinition(
                title="non editable field", max_length=100
            ),
        ),
    )


def test_relationship_to_one() -> None:
    dto_type = DjangoModelDTO[Book]
    field_defs = {f.name: f for f in dto_type.generate_field_definitions(Book)}

    assert field_defs["author"] == DTOFieldDefinition.from_field_definition(
        model_name="Book",
        default_factory=None,
        field_definition=FieldDefinition.from_annotation(
            Author,
            name="author",
            kwarg_definition=KwargDefinition(title="author"),
        ),
        dto_field=DTOField(),
    )


def test_many_to_one() -> None:
    dto_type = DjangoModelDTO[Author]
    field_defs = {f.name: f for f in dto_type.generate_field_definitions(Author)}

    assert field_defs["books"] == DTOFieldDefinition.from_field_definition(
        model_name="Author",
        default_factory=list,
        dto_field=DTOField("read-only"),
        field_definition=FieldDefinition.from_annotation(
            List[Book],
            name="books",
            kwarg_definition=KwargDefinition(
                title="books",
            ),
        ),
    )


def test_relationship_to_many() -> None:
    dto_type = DjangoModelDTO[Book]
    field_defs = {f.name: f for f in dto_type.generate_field_definitions(Book)}

    assert field_defs["genres"] == DTOFieldDefinition.from_field_definition(
        model_name="Book",
        default_factory=list,
        field_definition=FieldDefinition.from_annotation(
            List[Genre],
            name="genres",
            kwarg_definition=KwargDefinition(title="genres"),
        ),
        dto_field=DTOField(),
    )


def test_custom_fields() -> None:
    class MyDTO(DjangoModelDTO):
        custom_field_types = {MyStringField: str}

    dto_type = MyDTO[ModelWithFields]
    field_defs = {
        f.name: f for f in dto_type.generate_field_definitions(ModelWithFields)
    }

    assert field_defs[
        "custom_string_field"
    ] == DTOFieldDefinition.from_field_definition(
        model_name="ModelWithFields",
        default_factory=None,
        dto_field=DTOField(),
        field_definition=FieldDefinition.from_annotation(
            str,
            name="custom_string_field",
            kwarg_definition=KwargDefinition(
                title="custom string field",
            ),
        ),
    )
