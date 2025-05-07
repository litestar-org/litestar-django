# Litestar-Django

Django model support for Litestar, implemented via Litestar [DTOs](https://docs.litestar.dev/latest/usage/dto/index.html).

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

## Usage

### Directly constructing a DTO

```python
from litestar import get
from litestar_django import DjangoModelDTO
from app.models import Author

@get("/{author_id:int}", dto=DjangoModelDTO[Author])
async def handler(author_id: int) -> Author:
    return await Author.objects.prefetch_related("books").aget(id=author_id)
```

### Automatically creating DTOs via the plugin

```python
from litestar import get
from litestar_django import DjangoModelPlugin
from app.models import Author

@get("/{author_id:int}")
async def handler(author_id: int) -> Author:
    return await Author.objects.prefetch_related("books").aget(id=author_id)

app = Litestar([handler], plugins=[DjangoModelPlugin()])
```

### Creating a model instance from a DTO

```python
from typing import Annotated
from litestar import post
from litestar.dto import DTOConfig
from litestar_django import DjangoModelDTO
from app.models import Author

@post(
    "/",
    sync_to_thread=True,
    dto=DjangoModelDTO[
       Annotated[
          Author,
          # exclude primary key and relationship fields
          DTOConfig(exclude={"id", "books"})
       ]
    ],
    return_dto=DjangoModelDTO[Author],
)
async def handler(data: Author) -> Author:
    await data.asave()
    return data
```

## OpenAPI

Full OpenAPI schemas are generated from models based on their field types:

### Type map

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

### Additional properties

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

### Relationships

Relationships will be represented as individual components, referenced in the schema.


## Lazy loading

> [!IMPORTANT]
> Since lazy-loading is not supported in an async context, you must ensure to always
> load everything consumed by the DTO. Not doing so will result in a
> [`SynchronousOnlyOperation`](https://docs.djangoproject.com/en/5.2/ref/exceptions/#django.core.exceptions.SynchronousOnlyOperation)
> exception being raised by Django

This can be mitigated by:

1. Setting `include` or `exclude` rules to only include necessary fields ([docs](https://docs.litestar.dev/latest/usage/dto/1-abstract-dto.html#excluding-fields))
2. Configuring nested relationships with an appropriate `max_nexted_depth`
   ([docs](https://docs.litestar.dev/latest/usage/dto/1-abstract-dto.html#nested-fields))
3. Using [`select_related`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-related)
   and [`prefetch_related`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#prefetch-related)
   to ensure relationships are fully loaded


## Serialization / validation of 3rd party field types

Additionally, the following 3rd party fields / types are supported if the
`DjangoModelPlugin` is installed:

- `django-enumfields`
- `django-enumfields2`


## Contributing

All [Litestar Organization][litestar-org] projects are open for contributions of any
size and form.

If you have any questions, reach out to us on [Discord][discord] or our org-wide
[GitHub discussions][litestar-discussions] page.

<!-- markdownlint-disable -->
<hr />
<p align="center">
  <!-- github-banner-start -->
  <img src="https://raw.githubusercontent.com/litestar-org/branding/main/assets/Branding%20-%20SVG%20-%20Transparent/Organization%20Project%20-%20Banner%20-%20Inline%20-%20Dark.svg" alt="Litestar Logo - Light" width="40%" height="auto" />
  <br>An official <a href="https://github.com/litestar-org">Litestar Organization</a> Project
  <!-- github-banner-end -->
</p>

[litestar-org]: https://github.com/litestar-org
[discord]: https://discord.gg/litestar
[litestar-discussions]: https://github.com/orgs/litestar-org/discussions
