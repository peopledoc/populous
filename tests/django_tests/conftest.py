import os
import pytest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')


@pytest.fixture(autouse=True, scope='module')
def setup_django():
    django = pytest.importorskip('django')
    print(django.__dict__)
    django.setup()
