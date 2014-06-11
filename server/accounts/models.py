from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save


class UserProfile(models.Model):
    """ Additional data on top of Django User model """

    #: Django user instance (contains username, hashed password, etc).  This
    #: also forms the primary key, so ``User`` and ``UserProfile`` instances have
    #: the same primary key.
    user = models.OneToOneField(
        User, unique=True, primary_key=True, related_name="user")

    #: Mechanical Turk Worker ID
    mturk_worker_id = models.CharField(max_length=127, blank=True)

    #: block user (only locally; not on mturk)
    blocked = models.BooleanField(default=False)

    #: reason for blocking -- this will be displayed to the user
    blocked_reason = models.TextField(blank=True)

    #: if true, all HITs always get approved for this user (but the user still
    #: has to wait for consensus to get the feedback about their quality)
    always_approve = models.BooleanField(default=False)

    #: randomly exclude some users to measure their test error
    exclude_from_aggregation = models.BooleanField(default=False)

    def __unicode__(self):
        return self.user.__unicode__()

    def block(self, reason='', save=True):
        """ Block a user from performing *all* MTurk tasks.  Note that Amazon
        is not contacted and the worker's account is not flagged. """

        self.blocked = True
        self.blocked_reason = reason
        if save:
            self.save()
        print 'Blocking user: %s, reason: %s' % (self.user.username, self.blocked_reason)

    def unblock(self, save=True):
        """ Unblock a user (undo the ``self.block()`` operation). """

        self.blocked = False
        self.blocked_reason = ''
        if save:
            self.save()


#: The method get_profile() does not create a profile if one does not exist. You
#: need to register a handler for the User model's
#: django.db.models.signals.post_save signal and, in the handler, if created is
#: True, create the associated user profile:
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

post_save.connect(create_user_profile, sender=User)
