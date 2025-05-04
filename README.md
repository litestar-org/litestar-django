# Litestar-Django

Django model support for Litestar

```python
from litestar import get, Litestar
from litestar_django import DjangoModelPlugin
from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=100)


class Genre(models.Model):
    name = models.CharField(max_length=50)


class Book(models.Model):
    name = models.CharField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")
    genres = models.ManyToManyField(Genre, related_name="books")
    

@get("/{author_id:int}")
async def handler(author_id: int) -> Author:
    return await Author.objects.prefetch_related("books").aget(id=author_id)


app = Litestar([handler], plugins=[DjangoModelPlugin()])
```

This minimal setup will provide serialization of Django objects returned from handlers,
complete with OpenAPI schema generation.

## Installation

```bash
pip install litestar-django
```

## Features

### Serialization / validation

Serialization and validation of Django models, customizable via Litestar's [DTOs](https://docs.litestar.dev/latest/usage/dto)


### OpenAPI

Full OpenAPI schemas are generated from models based on their field types:

#### Type map

| Field                  | OpenAPI type | OpenAPI format |
|------------------------|--------------|----------------|
| `models.JSONField`     | `{}`         |                |
| `models.DecimalField`  | `number`     |                |
| `models.DateTimeField` | `string`     | `date-time`    |
| `models.DateField`     | `string`     | `date`         |
| `models.TimeField`     | `string`     | `duration`     |
| `models.DurationField` | `string`     | `duration`     |
| `models.FileField`     | `string`     |                |
| `models.FilePathField` | `string`     |                |
| `models.UUIDField`     | `string`     | `uuid`         |
| `models.IntegerField`  | `integer`    |                |
| `models.FloatField`    | `number`     |                |
| `models.BooleanField`  | `boolean`    |                |
| `models.CharField`     | `string`     |                |
| `models.TextField`     | `string`     |                |
| `models.BinaryField`   | `string`     | `byte`         |


#### Relationships

Relationships will be represented as individual components, referenced in the schema


#### Additional properties

The following properties are extracted from fields, in addition to its type:


| OpenAPI property   | From                 |
|--------------------|----------------------|
| `title`            | `Field.verbose_name` |
| `description`      | `Field.help_text`    |
| `enum`             | `Field.choices`      |
| `exclusiveMinimum` | `MinValueValidator`  |
| `exclusiveMaximum` | `MaxValueValidator`  |
| `minLength`        | `MinLengthValidator` |
| `maxLength`        | `MaxLengthValidator` |


