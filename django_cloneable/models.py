# encoding: utf-8
from django.db import models


__all__ = ('CloneableMixin',)


# Based on http://djangosnippets.org/snippets/1271/
class ModelCloneHelper(object):
    def __init__(self, instance):
        self.instance = instance

    def _clone_copy(self):
        import copy
        if not self.instance.pk:
            raise ValueError('Instance must be saved before it can be cloned.')
        return copy.copy(self.instance)

    def _clone_prepare(self, duplicate, exclude=None):
        # Setting pk to None tricks Django into not trying to overwrite the old
        # object (we will force the INSERT later)
        def unset_pk_and_parent_relation(cls):
            meta = cls._meta
            setattr(duplicate, meta.pk.attname, None)
            for parent, field in meta.parents.items():
                unset_pk_and_parent_relation(parent)

        unset_pk_and_parent_relation(duplicate.__class__)

        exclude = exclude or []
        for field in self.instance._meta.fields:
            # Fields given as list in ``exclude`` will be assigned the field's
            # default value. That makes it possible to exclude fields from
            # cloning.
            if field.name in exclude:
                setattr(duplicate, field.attname, field.get_default())
            # TODO: Is this really needed?
            # update auto_now(_add) fields
            if isinstance(field, (
                    models.DateField,
                    models.TimeField,
                    models.DateTimeField)):
                if field.auto_now or field.auto_now_add:
                    field.pre_save(duplicate, True)  # clone is an add, always

    def _clone_attrs(self, duplicate, attrs, exclude=None):
        """
        Will apply the ``attrs`` (a ``dict``) to the given instance. That makes
        it possible to exclude fields from cloning.
        """
        if attrs:
            for attname, value in attrs.iteritems():
                setattr(duplicate, attname, value)

    def _clone_copy_m2m(self, duplicate, exclude=None):
        exclude = exclude or []
        # copy.copy loses all ManyToMany relations.
        for field in self.instance._meta.many_to_many:
            # Skip this field.
            if field.name in exclude:
                continue
            # handle m2m using through
            if field.rel.through and not field.rel.through._meta.auto_created:
                # through-model must be cloneable
                if hasattr(field.rel.through, 'clone'):
                    qs = field.rel.through._default_manager.filter(
                        **{field.m2m_field_name(): self.instance})
                    for m2m_obj in qs:
                        m2m_obj.clone(attrs={
                            field.m2m_field_name(): duplicate
                        })
                else:
                    qs = field.rel.through._default_manager.filter(
                        **{field.m2m_field_name(): self.instance})
                    for m2m_obj in qs:
                        # TODO: Allow switching to different helper?
                        m2m_clone_helper = ModelCloneHelper(m2m_obj)
                        m2m_clone_helper.clone(attrs={
                            field.m2m_field_name(): duplicate
                        })
            # normal m2m, this is easy
            else:
                objs = getattr(self.instance, field.attname).all()
                setattr(duplicate, field.attname, objs)

    def _clone_copy_reverse_m2m(self, duplicate, exclude=None):
        exclude = exclude or []
        qs = self.instance._meta.get_all_related_many_to_many_objects()
        for relation in qs:
            # handle m2m using through
            if (
                    relation.field.rel.through and
                    not relation.field.rel.through._meta.auto_created):
                # Skip this field.
                # TODO: Not sure if this is the right value to check for..
                if relation.field.rel.related_name in exclude:
                    continue
                # through-model must be cloneable
                if hasattr(relation.field.rel.through, 'clone'):
                    qs = relation.field.rel.through._default_manager.filter(**{
                        relation.field.m2m_reverse_field_name(): self.instance
                    })
                    for m2m_obj in qs:
                        m2m_obj.clone(attrs={
                            relation.field.m2m_reverse_field_name(): duplicate
                        })
                else:
                    qs = relation.field.rel.through._default_manager.filter(**{
                        relation.field.m2m_reverse_field_name(): self.instance
                    })
                    for m2m_obj in qs:
                        # TODO: Allow switching to different helper?
                        m2m_clone_helper = ModelCloneHelper(m2m_obj)
                        m2m_clone_helper.clone(attrs={
                            relation.field.m2m_reverse_field_name(): duplicate
                        })
            # normal m2m, this is easy
            else:
                # Skip this field.
                if relation.field.rel.related_name in exclude:
                    continue
                objs_rel_manager = getattr(
                    self.instance,
                    relation.field.rel.related_name)
                objs = objs_rel_manager.all()
                setattr(duplicate, relation.field.rel.related_name, objs)

    def clone(self, attrs=None, commit=True, m2m_clone_reverse=True,
              exclude=None):
        """Returns a new copy of the current object"""

        clone_copy = getattr(self.instance, '_clone_copy', self._clone_copy)
        duplicate = clone_copy()

        clone_prepare = getattr(self.instance, '_clone_prepare',
                                self._clone_prepare)
        clone_prepare(duplicate, exclude=exclude)

        clone_attrs = getattr(self.instance, '_clone_attrs', self._clone_attrs)
        clone_attrs(duplicate, attrs, exclude=exclude)

        def clone_m2m(clone_reverse=m2m_clone_reverse):
            clone_copy_m2m = getattr(self.instance, '_clone_copy_m2m',
                                     self._clone_copy_m2m)
            clone_copy_m2m(duplicate, exclude=exclude)
            if clone_reverse:
                clone_copy_reverse_m2m = getattr(
                    self.instance,
                    '_clone_copy_reverse_m2m',
                    self._clone_copy_reverse_m2m)
                clone_copy_reverse_m2m(duplicate, exclude=exclude)

        if commit:
            duplicate.save(force_insert=True)
            clone_m2m()
        else:
            duplicate.clone_m2m = clone_m2m
        return duplicate


class CloneableMixin(models.Model):
    ''' Adds a clone() method to models

    Cloning is done by first copying the object using copy.copy. After this
    the primary key (pk) is removed, passed attributes are set
    (obj.clone(attrs={…})).

    If commit=True (default) all m2m relations will be cloned and saved, too.
    This includes reverse m2m relations, except if you pass
    m2m_clone_reverse=False. Even intermediate m2m relations (through model)
    will be cloned, when the intermediate model itself is cloneable (has a
    clone method, does not need to use CloneableMixin, but needs to allow at
    least passing attrs and doing an a automated save like commit=True).

    If you don't want the object to be saved directly (commit=False), the clone
    will get an additional clone_m2m method, so you can handle m2m relations
    outside of clone() (see Django forms save_m2m()). This method will save
    reverse m2m relations, if m2m_clone_reverse was True (default). Besides you
    may overwrite this behaviour by passing clone_reverse=True/False.

    clone() uses some helper methods, which may be extended/replaced in
    child classes. These include:
     * _clone_copy(): create the copy
     * _clone_prepare(): prepare the obj, so it can be saved
       (currently only removed pk and updated auto_now(_add) fields)
     * _clone_attrs(): set all attributes passed to clone()
     * _clone_copy_m2m(): clones all m2m relations
     * _clone_copy_reverse_m2m(): clones all reverse m2m relations
    '''

    CLONE_HELPER_CLASS = ModelCloneHelper

    def _clone_copy(self):
        return self._clone_helper._clone_copy()

    def _clone_prepare(self, duplicate, exclude=None):
        return self._clone_helper._clone_prepare(duplicate, exclude=exclude)

    def _clone_attrs(self, duplicate, attrs, exclude=None):
        return self._clone_helper._clone_attrs(duplicate, attrs,
                                               exclude=exclude)

    def _clone_copy_m2m(self, duplicate, exclude=None):
        return self._clone_helper._clone_copy_m2m(duplicate, exclude=exclude)

    def _clone_copy_reverse_m2m(self, duplicate, exclude=None):
        return self._clone_helper._clone_copy_reverse_m2m(duplicate,
                                                          exclude=exclude)

    def clone(self, attrs=None, commit=True, m2m_clone_reverse=True,
              exclude=None):
        """Returns a new copy of the current object"""
        self._clone_helper = self.CLONE_HELPER_CLASS(self)

        duplicate = self._clone_copy()
        self._clone_prepare(duplicate, exclude=exclude)
        self._clone_attrs(duplicate, attrs, exclude=exclude)

        def clone_m2m(clone_reverse=m2m_clone_reverse):
            self._clone_copy_m2m(duplicate, exclude=exclude)
            if clone_reverse:
                self._clone_copy_reverse_m2m(duplicate, exclude=exclude)
            del self._clone_helper

        if commit:
            duplicate.save(force_insert=True)
            clone_m2m()
        else:
            duplicate.clone_m2m = clone_m2m

        return duplicate

    class Meta:
        abstract = True
