import os
import json
import traceback
from decimal import Decimal

from celery import shared_task
from clint.textui import progress

from django.conf import settings
from django.db import transaction
from django.db.models import F, Count
from django.contrib.contenttypes.models import ContentType

from accounts.models import UserProfile
from mturk.models import Experiment, PendingContent, \
    MtHit, MtHitType, MtAssignment, MtSubmittedContent, \
    get_or_create_hit_type_from_experiment

from mturk.utils import get_mturk_connection, get_mturk_balance, \
    fetch_hit_contents
from common.utils import single_instance_task, get_content_tuple


@single_instance_task(timeout=12 * 3600)
@shared_task
def mturk_iteration_task(show_progress=False):
    """ Update votes and start new tasks """
    if not settings.MTURK_PIPELINE_ENABLE:
        print "mturk_iteration_task: Not running since MTURK_PIPELINE_ENABLE=%s" % (
            settings.MTURK_PIPELINE_ENABLE)
        return
    if not os.path.isfile('manage.py'):
        raise RuntimeError('Worker not in server directory')
    if os.path.exists('.disable-mturk'):
        print "mturk_iteration_task: Not running since .disable-mturk file exists"
        return
    #mturk_update_votes_cubam_task(show_progress=show_progress)
    consume_pending_objects_task()
    if settings.MTURK_CONFIGURE_QUALIFICATIONS:
        configure_qualifications_task()


@shared_task
def sync_hit_task(hit_id):
    """ Atomically sync a HIT with Amazon MTurk (with respect to the other
    tasks described as "atomic") """
    with transaction.atomic():
        # Note: select_for_update() locks the object for modification
        MtHit.objects.select_for_update().get(id=hit_id).sync_status()


@shared_task
def expire_hit_task(hit_id):
    """ Atomically expire a HIT (with respect to the other tasks described as
    "atomic") """
    try:
        with transaction.atomic():
            # Note: select_for_update() locks the object for modification
            MtHit.objects.select_for_update().get(id=hit_id).expire()
    except MtHit.DoesNotExist:
        get_mturk_connection().expire_hit(hit_id)


@shared_task
def approve_assignment_task(assignment_id, feedback, bonus_price=None, bonus_reason=''):
    """ Atomically approve a HIT (with respect to the other tasks described as
    "atomic") """
    with transaction.atomic():
        try:
            # Note: select_for_update() locks the object for modification
            asst = MtAssignment.objects.select_for_update().get(id=assignment_id)
            asst.approve(feedback=feedback)
            if bonus_price:
                asst.grant_bonus(price=bonus_price, reason=bonus_reason)

        except Exception as exc:
            raise mturk_submit_task.retry(exc=exc, countdown=300)


@shared_task
def reject_assignment_task(assignment_id, feedback):
    """ Atomically reject a HIT (with respect to the other tasks described as
    "atomic") """
    with transaction.atomic():
        try:
            # Note: select_for_update() locks the object for modification
            MtAssignment.objects.select_for_update().get(id=assignment_id) \
                .reject(feedback=feedback)
        except Exception as exc:
            raise mturk_submit_task.retry(exc=exc, countdown=300)


@shared_task
def increment_hit_counter_task(hit_id, counter_field, delta=1):
    """ Atomically increment a counter in a HIT """
    kwargs = {counter_field: F(counter_field) + delta}
    MtHit.objects.filter(id=hit_id).update(**kwargs)


@shared_task
def mturk_submit_task(**kwargs):
    """ Add submitted results to the database """

    try:
        with transaction.atomic():
            mturk_submit_impl(**kwargs)
    except Exception as exc:
        # Re-add to the queue so that we don't lose tasks
        print 'Exception (%s) -- will retry in 5 minutes' % exc
        traceback.print_exc()
        raise mturk_submit_task.retry(exc=exc, countdown=60 * 5)


def mturk_submit_impl(**kwargs):
    #slug = kwargs['experiment'].slug
    #print '%s time_ms: %s, time_active_ms: %s, time_load_ms: %s' % (
        #slug, kwargs['time_ms'], kwargs['time_active_ms'],
        #kwargs['time_load_ms'])
    #print '%s results: %s' % (slug, kwargs['results'])
    #if kwargs['mturk_assignment'].feedback:
        #print '%s feedback: %s' % (slug, kwargs['mturk_assignment'].feedback)

    # fetch objects if passed by ID
    if 'user_id' in kwargs:
        kwargs['user'] = UserProfile.objects.get(user_id=kwargs['user_id'])
    if 'mturk_hit_id' in kwargs:
        kwargs['mturk_hit'] = MtHit.objects.get(id=kwargs['mturk_hit_id'])
    if 'mturk_assignment_id' in kwargs:
        kwargs['mturk_assignment'] = MtAssignment.objects.get(id=kwargs['mturk_assignment_id'])
    if 'experiment_id' in kwargs:
        kwargs['experiment'] = Experiment.objects.get(id=kwargs['experiment_id'])

    # fetch experiment settings
    hit_type = kwargs['mturk_hit'].hit_type
    exp_settings = hit_type.experiment_settings
    if not exp_settings:
        # if the settings are somehow missing, update all records with the
        # newest experiment settings
        exp_settings = kwargs['experiment'].new_hit_settings
        MtHitType.objects.filter(id=hit_type.id) \
            .update(experiment_settings=exp_settings)

    # fetch hit contents
    if 'hit_contents' not in kwargs:
        kwargs['hit_contents'] = fetch_hit_contents(kwargs['mturk_hit'])
    hit_contents = kwargs['hit_contents']

    # new_objects_dict: {(content_type_id, content_id): [created items]}
    # (if [created items] is empty, the entry may be omitted)
    if hit_contents:
        new_objects_dict = exp_settings.out_content_model() \
            .mturk_submit(**kwargs)
    else:
        print "WARNING: no hit_contents in %s" % kwargs['mturk_hit'].id
        new_objects_dict = {}

    # sanity check
    if not all(isinstance(k, tuple) for k in new_objects_dict):
        raise ValueError(
            "Invalid new_objects_dict: %s" % repr(new_objects_dict))

    # flatten all items into one list
    new_objects_list = []
    for obj_list in new_objects_dict.values():
        new_objects_list += obj_list

    # attach objects to assignment
    for obj in new_objects_list:
        MtSubmittedContent.objects.get_or_create(
            assignment=kwargs['mturk_assignment'],
            object_id=obj.id,
            content_type=ContentType.objects.get_for_model(obj),
        )

    for content in hit_contents:
        # content_tuple: (content type id, object id)
        content_tuple = get_content_tuple(content)
        if content_tuple not in new_objects_dict:
            # print '%s: no new objects generated' % repr(content_tuple)
            continue

        delta_completed = len(new_objects_dict[content_tuple])
        delta_scheduled = exp_settings.out_count_ratio

        # update the fact that some outputs have been completed
        PendingContent.objects \
            .filter(
                experiment=kwargs['experiment'],
                content_type=ContentType.objects.get_for_id(content_tuple[0]),
                object_id=content_tuple[1],
            ).update(
                num_outputs_completed=F(
                    'num_outputs_completed') + delta_completed,
                num_outputs_scheduled=F(
                    'num_outputs_scheduled') - delta_scheduled,
            )

    # consider all affected objects for new experiments
    pending_objects = list(set(hit_contents + new_objects_list))
    add_pending_objects_task.delay(
        [get_content_tuple(c) for c in pending_objects])

    # mark experiment as dirty
    Experiment.objects.filter(id=kwargs['experiment'].id) \
        .update(cubam_dirty=True)

    # here, "complete" means that the user actually submitted (and is not a
    # "partial submission", i.e. a background auto-submit performed by the
    # experiment script)
    if not kwargs['complete']:
        return

    # sync with mturk 30 minutes from now (it can take a while to update the
    # status; 1 minute is not enough)
    sync_hit_task.apply_async(
        args=[kwargs['mturk_hit'].id],
        countdown=30 * 60)

    # mark as done
    MtAssignment.objects.filter(id=kwargs['mturk_assignment'].id) \
        .update(submission_complete=True)


@shared_task
def scan_all_for_pending_objects_task(show_progress=False):
    """ Scan all models for candidates to add to pending tasks """
    content_types = set()
    for exp in Experiment.objects.all().order_by('updated'):
        if exp.new_hit_settings.content_type:
            content_types.add(exp.new_hit_settings.content_type.id)
    for id in content_types:
        # call synchronously -- won't use Celery
        model = ContentType.objects.get_for_id(id).model_class()
        if show_progress:
            print 'Scanning %s for pending objects...' % model
        add_pending_objects_task(model, show_progress=show_progress)


@shared_task
def add_pending_objects_task(list_or_model, show_progress=False):
    """ Adds/updates modified objects as inputs to experiments """

    if not list_or_model:
        return

    try:
        experiments = Experiment.objects.all() \
            .filter(new_hit_settings__auto_add_hits=True) \
            .prefetch_related('new_hit_settings')

        if isinstance(list_or_model, list):
            # convert list to a content_tuple list
            tuple_list = [
                (x if isinstance(x, tuple) else get_content_tuple(x))
                for x in list_or_model
            ]

            for exp in experiments:
                # find objects that match the experiment content type
                exp_ct = exp.new_hit_settings.content_type
                id_list = [obj_id for (ct_id, obj_id) in tuple_list
                           if ct_id == exp_ct.id]

                if id_list:
                    queryset = exp_ct.model_class().objects \
                        .filter(id__in=id_list)
                    add_pending_objects_impl(exp, queryset, show_progress)
        else:
            model = list_or_model
            ct = ContentType.objects.get_for_model(model)
            queryset = model.objects.all()
            for exp in experiments.filter(new_hit_settings__content_type=ct):
                add_pending_objects_impl(exp, queryset, show_progress)

    except Exception as exc:
        # Re-add to the queue so that we don't lose tasks
        print 'Exception (%s) -- will retry in 5 minutes' % exc
        traceback.print_exc()
        raise add_pending_objects_task.retry(exc=exc, countdown=60 * 5)


def add_pending_objects_impl(experiment, content_queryset, show_progress=False):

    if show_progress:
        print ''
        print 'experiment:', experiment

    # extract params from experiment
    exp_settings = experiment.new_hit_settings
    content_type = exp_settings.content_type
    content_model = exp_settings.content_model()
    out_content_model = exp_settings.out_content_model()

    # ids that fail the filter
    id_list_fail = content_queryset \
        .exclude(**json.loads(exp_settings.content_filter)) \
        .distinct('id').order_by() \
        .values_list('id', flat=True)

    if show_progress:
        print 'id_list_fail:', len(id_list_fail)

    # objects that should be expired -- but don't expire the HIT
    if id_list_fail:
        pc_to_expire = PendingContent.objects \
            .filter(experiment=experiment,
                    num_outputs_max__gt=0,
                    object_id__in=id_list_fail)

        if show_progress:
            print 'pc_to_expire:', pc_to_expire.count()

        if pc_to_expire:
            pc_to_expire.update(num_outputs_max=0)

    # ids that pass the filter
    id_list_pass = content_queryset \
        .filter(**json.loads(exp_settings.content_filter)) \
        .distinct('id').order_by() \
        .values_list('id', flat=True)

    if show_progress:
        print 'id_list_pass:', len(id_list_pass)

    # update any existing objects with too few outputs
    num_outputs_max = experiment.new_hit_settings.num_outputs_max
    PendingContent.objects \
        .filter(experiment=experiment,
                num_outputs_max__lt=num_outputs_max,
                object_id__in=id_list_pass) \
        .update(num_outputs_max=num_outputs_max)

    # prepare list of objects already considered
    id_list_existing = PendingContent.objects \
        .filter(experiment=experiment,
                object_id__in=id_list_pass) \
        .distinct('object_id').order_by() \
        .values_list('object_id', flat=True)

    # update any existing complete items
    # if id_list_existing and hasattr(content_model, 'mturk_needs_more'):
        # complete_instances = PendingContent.objects \
            #.filter(experiment=experiment,
                    # object_id__in=id_list_existing,
                    # num_outputs_completed__gte=F('num_outputs_max')) \
            #.prefetch_related('content')
        # print 'updating existing items...'
        # with transaction.atomic():
            # complete_instances_iter = queryset_progress_bar(complete_instances) \
                # if show_progress else complete_instances.iterator()
            # for instance in complete_instances_iter:
                # if content_model.mturk_needs_more(instance.content):
                    # PendingContent.objects.filter(id=instance.id) \
                        #.update(num_outputs_max=1 +
                                # F('num_outputs_completed') +
                                # F('num_outputs_scheduled'))

    # exclude existing items to get the list of uncreated items
    id_list_new = list(set(id_list_pass).difference(set(id_list_existing)))

    # add new objects
    if id_list_new:
        print 'id_list_new:', len(id_list_new)
        has_invalid = ('invalid' in out_content_model._meta.get_all_field_names())
        if not has_invalid:
            print 'Note: model %s does not have field "invalid"' % out_content_model
        id_iterator = progress.bar(id_list_new) \
            if show_progress else id_list_new

        bulk_pc = []
        for id in id_iterator:
            obj = content_model.objects.get(id=id)
            priority = experiment.content_priority(obj)

            # count the number of items, minus invalid items (if invalid is
            # part of the model)
            filter_dict = {
                exp_settings.out_content_attr: obj,
                'mturk_assignment__hit__hit_type__experiment__completed_id': experiment.completed_id,
            }
            if has_invalid:
                filter_dict['invalid'] = False
            num_outputs_completed = out_content_model.objects \
                .filter(**filter_dict).count()

            bulk_pc.append(PendingContent(
                experiment=experiment,
                content_type=content_type,
                object_id=id,
                num_outputs_max=num_outputs_max,
                num_outputs_completed=num_outputs_completed,
                priority=priority,
            ))

            if len(bulk_pc) > 1000:
                PendingContent.objects.bulk_create(bulk_pc)
                bulk_pc = []
        PendingContent.objects.bulk_create(bulk_pc)


@shared_task
def consume_pending_objects_task(
        scan_for_pending_objects=True, clean_up_invalid=True, show_progress=False):
    """ IMPORTANT: only one instance of this function can be running at once.
    This uses both cache locking and filesystem locking to make sure.
    Lock-directory: .consume_pending_objects_task """

    if not os.path.isfile('manage.py'):
        raise RuntimeError('Worker not in server directory')

    # use a lock directory to ensure only one thread is running
    try:
        os.mkdir('.consume_pending_objects_task')
    except:
        print ("Already running!  If you are *sure* that " +
               "consume_pending_objects_task is not running, " +
               "delete the .consume_pending_objects_task directory")
        return

    try:
        # might as well scan again since the rest of this function is optimized
        if scan_for_pending_objects:
            scan_all_for_pending_objects_task(show_progress=show_progress)

        total_reward = Decimal('0.00')
        commission = Decimal(str(settings.MTURK_COMMISSION))

        # check all experiments for pending_contents
        pending_experiments = Experiment.objects \
            .filter(new_hit_settings__auto_add_hits=True) \
            .annotate(num=Count('pending_contents')) \
            .filter(num__gt=0)

        # make sure we are within budget
        balance = get_mturk_balance()
        print 'balance: %s' % balance

        for experiment in pending_experiments:
            exp_settings = experiment.new_hit_settings

            # (double filter since the keyword is the same)
            get_pending_contents = lambda: experiment.pending_contents \
                .filter(num_outputs_max__gt=0) \
                .filter(num_outputs_max__gt=(
                        F('num_outputs_completed') + F('num_outputs_scheduled'))) \
                .order_by('-num_outputs_completed', '-priority')

            pending_contents = get_pending_contents()
            num_pending_contents = pending_contents.count()

            if num_pending_contents < 1:
                continue

            if clean_up_invalid:
                if show_progress:
                    print '%s: clean up invalid or deleted content...' % experiment.slug

                pending_contents_dirty = False
                tuples = pending_contents.values_list('object_id', 'content_type')
                content_type_ids = set(t[1] for t in tuples)
                for ct_id in content_type_ids:
                    ct = ContentType.objects.get_for_id(id=ct_id)
                    pending_object_ids = [
                        t[0] for t in tuples if t[1] == ct_id]
                    model = ct.model_class()
                    existing_qset = model.objects.filter(id__in=pending_object_ids)
                    if hasattr(model, 'invalid'):
                        existing_qset = existing_qset.filter(invalid=False)
                    existing_object_ids = set(
                        existing_qset.values_list('id', flat=True))
                    to_delete = [
                        id for id in pending_object_ids if id not in existing_object_ids]
                    if to_delete:
                        print 'Deleting: %s dangling pending contents' % len(to_delete)
                        pending_contents.filter(
                            content_type=ct, object_id__in=to_delete).delete()
                        pending_contents_dirty = True
                if pending_contents_dirty:
                    pending_contents = get_pending_contents()
                    num_pending_contents = pending_contents.count()
                    if num_pending_contents < 1:
                        continue

                if show_progress:
                    print '%s: clean up invalid or deleted content... done' % experiment.slug

            # keep track of hit counts
            num_active_hits = MtHit.objects.filter(
                sandbox=settings.MTURK_SANDBOX,
                hit_type__experiment=experiment,
                all_submitted_assignments=False,
                expired=False,
            ).count()

            num_total_hits = MtHit.objects.filter(
                sandbox=settings.MTURK_SANDBOX,
                hit_type__experiment=experiment,
            ).count()

            print 'Experiment %s: %s/%s pending contents, %s/%s active HITs, %s/%s total HITs' % (
                experiment, num_pending_contents, exp_settings.contents_per_hit,
                num_active_hits, exp_settings.max_active_hits,
                num_total_hits, exp_settings.max_total_hits
            )

            hit_type = None
            while (num_active_hits < exp_settings.max_active_hits and
                   num_total_hits < exp_settings.max_total_hits and
                   pending_contents.count() >= exp_settings.contents_per_hit and
                   total_reward + settings.MTURK_MIN_BALANCE < balance):

                # transaction to ensure that if this fails, the pending_content
                # list is still consistent
                with transaction.atomic():

                    # lazily create hit_type
                    if not hit_type:
                        hit_type = get_or_create_hit_type_from_experiment(
                            experiment)

                    # attach contents to hit
                    cur_pending_contents = list(
                        pending_contents[:exp_settings.contents_per_hit])

                    num_to_schedule = None
                    if cur_pending_contents:
                        num_to_schedule = max(
                            [c.num_to_schedule() for c in cur_pending_contents])
                    if not num_to_schedule:
                        num_to_schedule = exp_settings.num_outputs_max

                    max_assignments = (
                        (num_to_schedule + exp_settings.out_count_ratio - 1) /
                        exp_settings.out_count_ratio
                    )
                    if max_assignments < 1:
                        continue

                    # create hit (also sends to amazon)
                    hit = MtHit.objects.create(
                        hit_type=hit_type,
                        lifetime=exp_settings.lifetime,
                        max_assignments=max_assignments)

                    total_reward += (hit_type.reward *
                                     hit.max_assignments * (1 + commission))
                    num_active_hits += 1
                    num_total_hits += 1

                    for pending_content in cur_pending_contents:

                        hit.contents.create(
                            content_type=pending_content.content_type,
                            object_id=pending_content.object_id)

                        # link HIT
                        pending_content.hits.add(hit)

                        # update scheduling count
                        PendingContent.objects.filter(id=pending_content.id).update(
                            num_outputs_scheduled=(
                                F('num_outputs_scheduled') +
                                max_assignments * exp_settings.out_count_ratio),
                        )

                    hit.num_contents = hit.contents.count()
                    hit.save()

                    print '%s: create hit: %s (%s assignments, %s contents)' % (
                        experiment, hit, max_assignments, hit.num_contents)

                # refresh for next loop
                pending_contents = get_pending_contents()

    finally:
        os.rmdir('.consume_pending_objects_task')

    if total_reward > 0:
        print 'added reward: %s' % total_reward
        print 'account balance: %s' % get_mturk_connection().get_account_balance()


@shared_task
def mturk_update_votes_cubam_task(show_progress=False):
    # use a lock directory to ensure only one thread is running
    LOCK_DIR = '.mturk_update_votes_cubam_task'
    try:
        os.mkdir(LOCK_DIR)
    except:
        print ("Already running!  If you are *sure* that " +
               "mturk_update_votes_cubam_task is not running, " +
               "delete the .mturk_update_votes_cubam_task directory")
        return

    try:
        from common.utils import import_modules
        modules = import_modules(settings.MTURK_MODULES)

        for mt1 in modules:
            if not hasattr(mt1, 'update_votes_cubam'):
                continue

            print '\nStarting: %s.update_votes_cubam()' % mt1.__name__
            changed_objects = mt1.update_votes_cubam(
                show_progress=show_progress)

            if changed_objects:
                # update pending contents
                add_pending_objects_task.delay(
                    [get_content_tuple(c) for c in changed_objects])

                # other updates
                for mt2 in modules:
                    if hasattr(mt2, 'update_changed_objects'):
                        mt2.update_changed_objects(changed_objects)

            print '\nDone: %s.update_votes_cubam()' % mt1.__name__
    finally:
        os.rmdir(LOCK_DIR)


@shared_task
def expire_invalid_hits(show_progress=False):
    """ Removes HITs that have contents that should not be part of an experiment """

    iterator = MtHit.objects.filter(expired=False)
    if show_progress:
        iterator = progress.bar(
            iterator.iterator(), expected_size=iterator.count())
    else:
        iterator = iterator.iterator()

    for hit in iterator:
        exp_set = hit.hit_type.hit_settings
        if not any(exp_set.obj_passes_filter(c.content)
                   for c in hit.contents.all()):
            try:
                hit.expire()
            except Exception as exc:
                print exc
                # traceback.print_exc()
            break


@shared_task
def configure_qualifications_task():
    if settings.MTURK_SANDBOX:
        return

    from common.utils import import_modules
    modules = import_modules(settings.MTURK_MODULES)

    for m in modules:
        if hasattr(m, 'configure_qualifications'):
            print 'Configuring qualifications: %s' % m.__name__
            m.configure_qualifications()
