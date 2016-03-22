from datetime import date
from django.test import TestCase

from .models import ModelWithCustomPK
from .models import ModelWithFields


class CloneableTests(TestCase):
    def test_cloning_generates_a_new_instance(self):
        i1 = ModelWithFields.objects.create(
            char='custom value',
            integer=23,
            date=date(2015, 12, 31))

        i2 = i1.clone()

        assert i2.pk is not None
        assert i1.pk != i2.pk
        assert i1.char == i2.char
        assert i1.integer == i2.integer
        assert i1.date == i2.date

    def test_must_provide_new_pk_if_its_custom_field(self):
        i1 = ModelWithCustomPK.objects.create(key='foo', value=42)
        i2 = i1.clone(attrs={'key': 'bar'})

        assert i2.pk == 'bar'
        assert i1.pk != i2.pk
        assert i2.value == 42
