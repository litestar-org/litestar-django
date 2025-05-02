import os

import django


os.environ["DJANGO_SETTINGS_MODULE"] = "tests.some_app.settings"

django.setup()

# @pytest.fixture(scope="session", autouse=True)
# def django_setup(monkeypatch) -> None:
