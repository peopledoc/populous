import os
import pytest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')


@pytest.fixture(autouse=True)
def setup_django():
    django = pytest.importorskip('django')
    django.setup()
