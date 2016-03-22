django-cloneable
================

|pypi-badge| |build-status|

.. |build-status| image:: https://travis-ci.org/team23/django_cloneable.svg
    :target: https://travis-ci.org/team23/django_cloneable

.. |pypi-badge| image:: https://img.shields.io/pypi/v/django-admin-cloneable.svg
    :target: https://pypi.python.org/pypi/django-cloneable

**django-cloneable** provides a ``CloneableMixin`` class that has a ``clone()``
method. It can be mixed into any Django model.

The ``clone()`` method must be called on an already saved instance (one that
has ``pk`` set). It then returns a new instance of the model that has all the
same field values as the original instance, but it will be a seperate database
row with a distinct primary key.

An example:

.. code:: python

    from django.db import models
    from django_cloneable import CloneableMixin

    class Ingredient(CloneableMixin, models.Model):
        name = models.CharField(max_length=50)
        is_spicy = models.BooleanField(default=False)

    class Pizza(CloneableMixin, models.Model):
        name = models.CharField(max_length=50)
        price = models.IntegerField()
        ingredients = models.ManyToManyField(Ingredient)

    tomatos = Ingredient.objects.create(name='Tomato', is_spicy=False)
    cheese = Ingredient.objects.create(name='Cheese', is_spicy=False)
    chili = Ingredient.objects.create(name='Chili', is_spicy=True)

    margarita = Pizza.objects.create(name='Margarita')
    margarita.ingredients.add(tomatos)
    margarita.ingredients.add(cheese)

    diabolo = margarita.clone(attrs={'name': 'Diabolo'})
    diabolo.ingerdients.add(chili)

    # Nothing has changed on the original instance.
    assert margarita.name == 'Margarita'
    assert margarita.ingredients.all() == [tomatos, cheese]

    # The original m2m values were copied, and the new values were added.
    assert diabolo.name == 'Diabolo'
    assert diabolo.ingredients.all() == [tomatos, cheese, chili]

As shown in the example, you can provide the ``attrs`` that shall be replaced
in the cloned object. That lets you change the cloned instance before it gets
saved. By default the clone will be saved to the database, so that it has
``pk`` when it gets returned.

There are numerous hooks on how you can modify the cloning logic. The best way
to learn about them is to have a look at the implementation of
``CloneableMixin``.

Development
-----------

Install the dependencies (including the test dependencies) with::

    pip install -r requirements.txt

Then you can run all tests with::

    tox
