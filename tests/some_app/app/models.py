import enum

import enumfields
from django.core import validators
from django.db import models


class StdEnum(enum.StrEnum):
    ONE = "ONE"
    TWO = "TWO"


class LabelledEnum(enumfields.Enum):
    ONE = "ONE"
    TWO = "TWO"

    class Labels:
        ONE = "One"
        TWO = "Two"


def make_default() -> str:
    return "Hello"


class MyStringField(models.Field):
    pass


class ModelWithFields(models.Model):
    json_field = models.JSONField()
    decimal_field = models.DecimalField()
    datetime_field = models.DateTimeField()
    date_field = models.DateField()
    time_field = models.TimeField()
    duration_field = models.DurationField()
    file_field = models.FileField()
    file_path_field = models.FilePathField()
    uuid_field = models.UUIDField()
    integer_field = models.IntegerField()
    float_field = models.FloatField()
    bool_field = models.BooleanField()
    char_field = models.CharField()
    text_field = models.TextField()
    binary_field = models.BinaryField(
        editable=True,  # implicitly defaults to 'False'
    )

    nullable_field = models.CharField(null=True)
    field_with_default = models.CharField(null=True, default="hello")
    field_with_default_callable = models.CharField(null=True, default=make_default)
    field_with_help_text = models.CharField(help_text="This is a help text")
    renamed_field = models.CharField(verbose_name="That's not my name")

    non_editable_field = models.CharField(editable=False)

    min_1_int_field = models.IntegerField(validators=[validators.MinValueValidator(1)])
    min_2_max_5_int_field = models.IntegerField(
        validators=[
            validators.MinValueValidator(2),
            validators.MaxValueValidator(5),
        ],
    )

    min_1_str_field = models.CharField(validators=[validators.MinLengthValidator(1)])
    max_2_str_field = models.CharField(validators=[validators.MaxLengthValidator(2)])

    custom_string_field = MyStringField()

    enum_field = enumfields.EnumField(StdEnum)
    labelled_enum_field = enumfields.EnumField(LabelledEnum)

    field_with_choices = models.CharField(choices={"foo": "FOO", "bar": "BAR"})

    field_with_regex_validator = models.CharField(
        validators=[validators.RegexValidator(r"\d{3}")]
    )


class ModelInvalidRegexValidator(models.Model):
    invalid_regex_validator = models.CharField(
        validators=[validators.RegexValidator(r"\d", inverse_match=True)]
    )


class Author(models.Model):
    name = models.CharField(max_length=100)


class Genre(models.Model):
    name = models.CharField(max_length=50)


class Book(models.Model):
    name = models.CharField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")
    genres = models.ManyToManyField(Genre, related_name="books")
