from django.db import models
from django.utils.timezone import now

from django.contrib.contenttypes.models import ContentType

from accounts.models import UserProfile
from common.signals import marked_invalid


class EmptyModelBase(models.Model):
    """ Base class of all models, with no fields """

    def get_entry_dict(self):
        return {'id': self.id}

    def get_entry_attr(self):
        ct = ContentType.objects.get_for_model(self)
        return 'data-model="%s/%s" data-id="%s"' % (
            ct.app_label, ct.model, self.id)

    def get_entry_id(self):
        ct = ContentType.objects.get_for_model(self)
        return '%s.%s.%s' % (ct.app_label, ct.model, self.id)

    class Meta:
        abstract = True
        ordering = ['-id']


class ModelBase(EmptyModelBase):
    """ Base class of all models, with an 'added' field """
    added = models.DateTimeField(default=now)

    class Meta:
        abstract = True
        ordering = ['-id']


class UserBase(ModelBase):
    """ Base class for a model that has users """

    #: User that created this object
    user = models.ForeignKey(UserProfile)

    class Meta:
        abstract = True
        ordering = ['-id']


class PaperCitation(models.Model):
    """ Paper citation for an intrinsic images algorithm """

    #: url-friendly name of the citation
    slug = models.CharField(unique=True, max_length=128)

    # short inline citation in the form "[author year]"
    inline_citation = models.CharField(blank=True, max_length=128)

    #: text version of the paper citation
    authors = models.TextField(blank=True)

    title = models.TextField(blank=True)

    journal = models.TextField(blank=True)

    #: URL to visit
    url = models.URLField(blank=True)

    def citation_html(self):
        if self.url:
            return '%s.  "%s".  <i>%s</i>.  <a href="%s">%s</a>.' % (self.authors, self.title, self.journal, self.url, self.url)
        else:
            return '%s.  "%s".  <i>%s</i>.' % (self.authors, self.title, self.journal)

    def inline_citation_html(self):
        if self.url:
            return "<a href='%s' target='_blank'>%s</a>" % (self.url, self.inline_citation)
        else:
            return self.inline_citation


class ResultBase(UserBase):
    """ Base class for objects created as a result of a submission """

    #: The MTurk Assignment that the user was in when this record was created
    mturk_assignment = models.ForeignKey(
        'mturk.MtAssignment', null=True, blank=True,
        related_name='+', on_delete=models.SET_NULL
    )

    #: True if created in the mturk sandbox
    sandbox = models.BooleanField(default=False)

    #: This has been marked by an admin as invalid or incorrect AND will be
    #: re-scheduled for new labeling.  This can happen when an experiment is
    #: changed and things need to be recomputed.
    invalid = models.BooleanField(default=False)

    #: The method by which the quality label was obtained
    QUALITY_METHODS = (
        ('A', 'admin'), ('C', 'CUBAM'),
        ('M', 'majority vote'), ('Q', 'qualification')
    )
    quality_method_to_str = dict((k, v) for (k, v) in QUALITY_METHODS)
    #: The method by which the quality label was obtained
    quality_method = models.CharField(
        max_length=1, choices=QUALITY_METHODS, blank=True, null=True)

    #: time taken to specify this label in ms
    time_ms = models.IntegerField(blank=True, null=True, db_index=True)

    #: time taken to specify this label in ms, excluding time that the user was
    #: in another window
    time_active_ms = models.IntegerField(blank=True, null=True, db_index=True)

    #: payment for this specific label
    reward = models.DecimalField(
        decimal_places=4, max_digits=8, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.id and self.mturk_assignment:
            self.sandbox = self.mturk_assignment.hit.sandbox
        if not self.reward:
            from common.utils import compute_label_reward
            self.reward = compute_label_reward(self)
        super(ResultBase, self).save(*args, **kwargs)

    def time_s(self):
        """ Time pretty-printed in seconds (helper for templates) """
        if self.time_ms:
            t = self.time_ms / 1000.0
            return round(t, 2 if t < 10 else 1)
        else:
            return None

    def time_active_s(self):
        """ Active pretty-printed time in seconds (helper for templates) """
        if self.time_active_ms:
            t = self.time_active_ms / 1000.0
            return round(t, 2 if t < 10 else 1)
        else:
            return None

    def mark_invalid(self, save=True):
        dirty = (not self.invalid)
        self.invalid = True
        self.quality_method = 'A'
        if save:
            self.save()
        if dirty:
            marked_invalid.send(sender=self.__class__, instance=self)

    def get_thumb_overlay(self):
        return self.__unicode__()

    class Meta:
        abstract = True
        ordering = ['-time_ms']
