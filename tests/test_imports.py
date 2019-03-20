def test_imports():
    import django_cloneable  # noqa
    from django_cloneable.models import CloneableMixin

    assert CloneableMixin is not None


def test_has_version():
    import django_cloneable

    assert django_cloneable.__version__.count('.') >= 2
