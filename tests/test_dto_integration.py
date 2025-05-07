import secrets
from typing import Annotated, Any

import pytest
from litestar import get, Response, Litestar, post
from litestar.dto import DTOConfig
from litestar.testing import create_test_client

from litestar_django.dto import DjangoModelDTO
from litestar_django.plugin import DjangoModelPlugin
from tests.some_app.app.models import (
    Author,
    Book,
    Genre,
    ModelWithFields,
    ModelWithCustomFields,
)


@pytest.mark.django_db(transaction=True)
def test_serialization() -> None:
    author = Author.objects.create(name="Peter")
    author_id = author.id

    @get("/one", dto=DjangoModelDTO[Author], sync_to_thread=True)
    def handler() -> Author:
        return Author.objects.prefetch_related("books").get(id=author_id)

    # this should also work if we return a list
    @get("/list", dto=DjangoModelDTO[Author], sync_to_thread=True)
    def handler_with_list() -> list[Author]:
        return [Author.objects.prefetch_related("books").get(id=author_id)]

    author_data = {"id": author.id, "name": author.name, "books": []}

    with create_test_client([handler, handler_with_list]) as client:
        res = client.get("/one")
        assert res.status_code == 200
        assert res.json() == author_data

        res = client.get("/list")
        assert res.status_code == 200
        assert res.json() == [author_data]


@pytest.mark.django_db(transaction=True)
def test_serialization_with_implicit_dto() -> None:
    author = Author.objects.create(name="Peter")
    author_id = author.id

    # we do not specify a DTO here; it is instead created implicitly by the plugin
    @get("/one", sync_to_thread=True)
    def handler() -> Author:
        return Author.objects.prefetch_related("books").get(id=author_id)

    # this should also work if we return a list
    @get("/list", sync_to_thread=True)
    def handler_with_list() -> list[Author]:
        return [Author.objects.prefetch_related("books").get(id=author_id)]

    # this should also work if we return a list
    @get("/response", sync_to_thread=True)
    def handler_with_response() -> Response[Author]:
        return Response(Author.objects.prefetch_related("books").get(id=author_id))

    author_data = {"id": author.id, "name": author.name, "books": []}

    with create_test_client(
        [handler, handler_with_list, handler_with_response],
        plugins=[DjangoModelPlugin()],
    ) as client:
        res = client.get("/one")
        assert res.status_code == 200
        assert res.json() == author_data

        res = client.get("/list")
        assert res.status_code == 200
        assert res.json() == [author_data]

        res = client.get("/response")
        assert res.status_code == 200
        assert res.json() == author_data


@pytest.mark.django_db(transaction=True)
def test_serialize_to_many() -> None:
    author = Author.objects.create(name="Someone")
    genre_a = Genre.objects.create(name="genre_a")
    genre_b = Genre.objects.create(name="genre_b")
    book_a = Book.objects.create(name="book_a", author=author)
    book_b = Book.objects.create(name="book_b", author=author)
    book_c = Book.objects.create(name="book_c", author=author)

    book_a.genres.set([genre_a])
    book_b.genres.set([genre_a, genre_b])

    @get(
        "/",
        dto=DjangoModelDTO[
            Annotated[
                Book,
                DTOConfig(
                    # set an exclusion here to break the recursion chain of book -> genres -> books
                    exclude={"genres.0.books"}
                ),
            ]
        ],
        sync_to_thread=True,
    )
    def handler() -> list[Book]:
        # need to prefetch here, so we don't accidentally perform lazy-loading during
        # the transfer process
        return list(Book.objects.prefetch_related("author", "genres").all())

    with create_test_client(
        [handler], raise_server_exceptions=True, debug=True
    ) as client:
        res = client.get("/")
        assert res.status_code == 200
        assert res.json() == [
            {
                "id": book_a.id,
                "name": "book_a",
                "author": {"id": author.id, "name": "Someone"},
                "genres": [{"id": genre_a.id, "name": "genre_a"}],
            },
            {
                "id": book_b.id,
                "name": "book_b",
                "author": {"id": author.id, "name": "Someone"},
                "genres": [
                    {"id": genre_a.id, "name": "genre_a"},
                    {"id": genre_b.id, "name": "genre_b"},
                ],
            },
            {
                "id": book_c.id,
                "name": "book_c",
                "author": {"id": author.id, "name": "Someone"},
                "genres": [],
            },
        ]


@pytest.mark.django_db(transaction=True)
def test_validate() -> None:
    @post(
        "/",
        sync_to_thread=True,
        dto=DjangoModelDTO[Annotated[Author, DTOConfig(exclude={"id", "books"})]],
        return_dto=DjangoModelDTO[Author],
    )
    def handler(data: Author) -> Author:
        data.save()
        return Author.objects.prefetch_related("books").get(id=data.id)

    with create_test_client([handler]) as client:
        author_name = secrets.token_hex()
        res = client.post("/", json={"name": author_name})
        assert res.status_code == 201
        author = Author.objects.get(name=author_name)
        assert res.json() == {"id": author.id, "name": author_name, "books": []}


@pytest.mark.django_db(transaction=True)
def test_enumfields() -> None:
    @post(
        "/",
        dto=DjangoModelDTO[Annotated[ModelWithCustomFields, DTOConfig(exclude={"id"})]],
    )
    async def post_handler(data: ModelWithCustomFields) -> dict[str, Any]:
        await data.asave()
        return {
            "id": data.id,
            "enum_field": data.enum_field.value,
            "enumfields_enum": data.enumfields_enum.value,
        }

    @get("/{obj_id:int}", dto=DjangoModelDTO[ModelWithCustomFields])
    async def get_handler(obj_id: int) -> ModelWithCustomFields:
        return await ModelWithCustomFields.objects.aget(id=obj_id)

    with create_test_client(
        [get_handler, post_handler], plugins=[DjangoModelPlugin()]
    ) as client:
        res = client.post("/", json={"enum_field": "ONE", "enumfields_enum": "TWO"})
        assert res.status_code == 201
        data = res.json()
        model_id = data.pop("id")
        assert data == {"enum_field": "ONE", "enumfields_enum": "TWO"}

        res = client.get(f"/{model_id}")
        assert res.status_code == 200
        assert res.json() == {"id": model_id, **data}


def test_schema() -> None:
    @get("/", dto=DjangoModelDTO[ModelWithFields], sync_to_thread=True)
    def handler() -> ModelWithFields:
        pass

    app = Litestar([handler])
    # ensure schema is valid
    app.openapi_schema
