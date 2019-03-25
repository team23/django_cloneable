from datetime import date
from django.db import models

from django_cloneable.models import CloneableMixin


class ModelWithFields(CloneableMixin, models.Model):
    char = models.CharField(max_length=50, default='')
    integer = models.IntegerField(default=0)
    date = models.DateField(default=date(2000, 1, 1))


class ModelWithCustomPK(CloneableMixin, models.Model):
    key = models.CharField(max_length=50, primary_key=True)
    value = models.IntegerField()
