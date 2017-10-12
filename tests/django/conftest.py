import os
import pytest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')


@pytest.fixture(autouse=True)
def setup_django():
    try:
        import django

        django.setup()
    except (ImportError, AttributeError):
        pytest.skip(msg="Django is not installed")
