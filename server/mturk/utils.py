import json
import datetime
from decimal import Decimal

from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from boto.mturk.connection import MTurkConnection, MTurkRequestError
from boto.mturk.qualification import Qualifications, \
    NumberHitsApprovedRequirement, PercentAssignmentsAbandonedRequirement, \
    PercentAssignmentsApprovedRequirement, PercentAssignmentsRejectedRequirement, \
    PercentAssignmentsReturnedRequirement, PercentAssignmentsSubmittedRequirement, \
    Requirement

from common.utils import has_foreign_key
from accounts.models import UserProfile


def aws_str_to_datetime(s):
    """ Parse Amazon date-time string """
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')


def get_mturk_connection():
    return MTurkConnection(
        aws_access_key_id=settings.MTURK_AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.MTURK_AWS_SECRET_ACCESS_KEY,
        host=settings.MTURK_HOST,
        debug=settings.MTURK_SANDBOX)


def get_mturk_balance():
    return Decimal(get_mturk_connection().get_account_balance()[0].amount)


def extract_mturk_attr(result_set, attr):
    """ Extracts an attribute from a boto ResultSet """

    if hasattr(result_set, attr):
        return getattr(result_set, attr)

    try:
        for r in result_set:
            if hasattr(r, attr):
                return getattr(r, attr)
    except TypeError:
        pass

    raise MTurkRequestError(status=0, reason='Missing %s in response' % attr)


def get_or_create_mturk_worker(mturk_worker_id):
    """ Returns a UserProfile object for the associated mturk_worker_id """
    if not mturk_worker_id:
        return None
    try:
        return UserProfile.objects.get(mturk_worker_id=mturk_worker_id)
    except UserProfile.DoesNotExist:
        user = User.objects.get_or_create(
            username='mturk_' + mturk_worker_id)[0]
        profile = user.get_profile()
        profile.mturk_worker_id = mturk_worker_id
        profile.save()
        return profile


def get_or_create_mturk_worker_from_request(request):
    if 'workerId' in request.GET:
        return get_or_create_mturk_worker(request.GET['workerId'])
    else:
        return None


def qualification_to_boto(*args):
    """ Convert a qualification to the format required by boto """

    if len(args) == 2:
        name = args[0]
        value = args[1]
    elif len(args) == 1:
        name = args[0].name
        value = args[0].value
    else:
        raise ValueError("Invalid arguments")

    from mturk.models import MtQualification
    try:
        q = MtQualification.objects.get(slug=name)
        return Requirement(
            qualification_type_id=q.id,
            comparator="EqualTo",
            integer_value=value)
    except MtQualification.DoesNotExist:
        pass

    if name == 'num_approved':
        return NumberHitsApprovedRequirement(
            comparator='GreaterThanOrEqualTo', integer_value=value)
    elif name == 'perc_abandoned':
        return PercentAssignmentsAbandonedRequirement(
            comparator='LessThanOrEqualTo', integer_value=value)
    elif name == 'perc_approved':
        return PercentAssignmentsApprovedRequirement(
            comparator='GreaterThanOrEqualTo', integer_value=value)
    elif name == 'perc_rejected':
        return PercentAssignmentsRejectedRequirement(
            comparator='LessThanOrEqualTo', integer_value=value)
    elif name == 'perc_returned':
        return PercentAssignmentsReturnedRequirement(
            comparator='LessThanOrEqualTo', integer_value=value)
    elif name == 'perc_submitted':
        return PercentAssignmentsSubmittedRequirement(
            comparator='GreaterThanOrEqualTo', integer_value=value)
    else:
        raise ValueError("Unknown name: %s" % name)


def qualification_dict_to_boto(quals):
    if not quals:
        return None
    quals_boto = filter(
        None, [qualification_to_boto(k, v) for k, v in quals.iteritems()])
    return Qualifications(quals_boto) if quals_boto else None


def get_content_model_prefetch(content_model, content_attr='content'):
    """ Returns the fields that should be prefetched, for a relation that
    starts with '<content_attr>__'.  If the model has MTURK_PREFETCH, then that
    is used.  Otherwise, some common attributes are tested (photo, shape) and
    used if those foreign keys exist.  """

    if hasattr(content_model, 'MTURK_PREFETCH'):
        return ['%s__%s' % (content_attr, k)
                for k in content_model.MTURK_PREFETCH]
    else:
        # guess if there is no default
        prefetch = []
        if has_foreign_key(content_model, 'photo'):
            prefetch.append('%s__photo' % content_attr)
        if has_foreign_key(content_model, 'shape'):
            prefetch.append('%s__shape' % content_attr)
            prefetch.append('%s__shape__photo' % content_attr)
        return prefetch


def get_model_prefetch(content_model):
    """ Returns the fields that should be prefetched, for a generic relation """

    if hasattr(content_model, 'MTURK_PREFETCH'):
        return content_model.MTURK_PREFETCH
    else:
        # guess if there is no default
        prefetch = []
        if has_foreign_key(content_model, 'photo'):
            prefetch.append('photo')
        if has_foreign_key(content_model, 'shape'):
            prefetch.append('shape')
            prefetch.append('shape__photo')
        return prefetch


def fetch_content_tuples(content_tuples):
    """ Fetch a list of generic items, given as a list of
    ```[(content_type_id, object_id), ...]``` """

    # group by content type
    ct_to_ids = {}
    for (ct, id) in content_tuples:
        if ct in ct_to_ids:
            ct_to_ids[ct].append(id)
        else:
            ct_to_ids[ct] = [id]

    # bulk fetch for each content type
    ct_to_values = {}
    for (ct, ids) in ct_to_ids.iteritems():
        model = ContentType.objects.get_for_id(ct).model_class()
        prefetch = get_model_prefetch(model)
        ct_to_values[ct] = model.objects \
            .select_related(*prefetch).in_bulk(ids)

    # match original ordering
    return [ct_to_values[ct][id] for (ct, id) in content_tuples]


def fetch_hit_contents(hit):
    """ Fetch the contents (the items shown the user) efficiently in a small
    number of queries """

    prefetch = ['content']
    content_type_ids = hit.contents.all() \
        .order_by().distinct('content_type') \
        .values_list('content_type', flat=True)

    if len(content_type_ids) == 1:
        content_model = ContentType.objects.get_for_id(
            content_type_ids[0]).model_class()
        prefetch += get_content_model_prefetch(content_model)
    #else:  TODO: handle this case efficiently (still works, just slow)

    contents = [p.content
                for p in hit.contents.all()
                .prefetch_related(*prefetch).order_by()]

    return filter(None, contents)


def configure_experiment(slug, variant='', **kwargs):
    """ Configures an experiment in the database
    (:class:`mturk.models.Experiment`).  To be called by
    :meth:`configure_experiments`.

    :param slug: unique human-readable ID (must be valid Python variable name).
        The ``slug`` and ``variant`` are together unique.

    :param variant: optional string that may be used to include multiple
        variations on the same experiment, where the same template and user
        interface is used across all variants.  The ``slug`` and ``variant``
        together are unique.
        Example: you want to perform object labeling, with different lists of
        allowed object names (see ``shapes.experiments`` for this example).

    :param completed_id: optional string that may be used in place of ``slug``
        when determining whether an experiment has been completed.  If two
        experiments share this field, then an item completed under one
        experiment will count as completed under the other experiment.

    :param template_dir: directory for templates, usually
        ``'<app>/experiments'``.
        The templates for each experiment are constructed as follows:

        ::

            {template_dir}/{slug}.html              -- mturk task
            {template_dir}/{slug}_inst_content.html -- instructions page (just the
                                                       content)
            {template_dir}/{slug}_inst.html         -- instructions (includes
                                                       _inst_content.html)
            {template_dir}/{slug}_tut.html          -- tutorial (if there is one)

    :param module: module containing the ``experiments.py`` file, usually
        ``'<app>.experiments'``

    :param examples_group_attr: the attribute used to group examples together.
        Example: if you have good and bad BRDFs for a shape, and the BRDF
        points to the shape with the name 'shape', then this field would could
        set to 'shape'.

    :param version: should be the value ``2`` (note that ``1`` is for the
        original OpenSurfaces publication).

    :param reward: payment per HIT, as an instance of ``decimal.Decimal``

    :param num_outputs_max: the number of output items that each input item
        will produce.  Usually this is ``1``.  An example of another value: for
        OpenSurfaces material segmentation, 1 photo will produce 6
        segmentations.

    :param contents_per_hit: the number of contents to include in each HIT

    :param test_contents_per_assignment: if specified, the number of
        secret test items to be added (on top of ``contents_per_hit``)
        to each HIT.

    :param has_tutorial: ``True`` if this experiment has a special
        tutorial (see ``intrinsic/experiments.py`` for an example).

    :param content_type_model: the model class for input content (content that
        is shown to the user)

    :param out_content_type_model: the model class for output (user responses)

    :param out_content_attr: on the output model class, the name of the
        attribute that gives the input for that output.  For example,
        for a material segmentation, a ``Photo`` is the input and a
        ``SubmittedShape`` is the output, and ``SubmittedShape.photo``
        gives the input photo.

    :param content_filter: a dictionary of filters to be applied
        to the input content to determine which items should be labeled.

        Example for labeling BRDFs:

        .. code-block:: py

            {
                'invalid': False,
                'pixel_area__gt': Shape.MIN_PIXEL_AREA,
                'num_vertices__gte': 10,
                'correct': True,
                'substance__isnull': False,
                'substance__fail': False,
                'photo__whitebalanced': True,
                'photo__scene_category_correct': True,
            }

    :param title: string shown in the MTurk marketplace as the title of the
        task.

    :param description: string shown in the MTurk marketplace describing the
        task.

    :param keywords: comma-separated string listing the keywords, e.g.
        ``'keyword1,keyword2,keyword3'``.

    :param frame_height: height in pixels used to display the iframe for
        workers.  Most workers have 1024x768 or 800x600 screen resolutions, so I
        recommend setting this to at most **668** pixels.  Alternatively,
        you could set it to a very large number and avoid an inner scroll bar.

    :param requirements: [deprecated feature] dictionary of requirements that
        users must satisfy to submit a task, or ``{}`` if there are no
        requirements.  These requirements are passed as context variables.  This is
        an old feature and is implemented very inefficiently.  There
        are better ways of getting data into the experiment context,
        such as :meth:`external_task_extra_context`.

    :param auto_add_hits: if ``True``, dispatch new HITs of this type.

    """

    # import locally to avoid circular import
    from mturk.models import Experiment, ExperimentExample, \
        ExperimentTestContent

    # create experiment object
    if not isinstance(variant, basestring):
        variant = json.dumps(variant)

    experiment, __ = Experiment.objects.get_or_create(
        slug=slug, variant=variant)

    # variables on experiment object
    experiment_dirty = False
    for k in ['name', 'completed_id', 'version', 'has_tutorial',
              'template_dir', 'module', 'examples_group_attr',
              'test_contents_per_assignment']:
        if k in kwargs:
            setattr(experiment, k, kwargs[k])
            del kwargs[k]
            experiment_dirty = True
    if experiment_dirty:
        experiment.save()

    # allow specifying objects instead of json strings
    for k in ('content_filter', 'requirements'):
        if k in kwargs and kwargs[k]:
            if isinstance(kwargs[k], basestring):
                # make sure it's valid json and remove any extra whitespace
                kwargs[k] = json.dumps(json.loads(kwargs[k]))
            else:
                kwargs[k] = json.dumps(kwargs[k])
        else:
            kwargs[k] = '{}'

    # allow specifying models instead of contenttype objects
    if 'content_type_model' in kwargs:
        kwargs['content_type'] = ContentType.objects.get_for_model(
            kwargs['content_type_model'])
        del kwargs['content_type_model']

    # make sure that the out_content_type also satisfies certain requirements
    if 'out_content_type_model' in kwargs:
        model = kwargs['out_content_type_model']

        # make sure certain methods and fields are implemented
        if not hasattr(model, 'mturk_submit'):
            raise NotImplementedError(
                "Model %s does not have a mturk_submit method" % model)
        if 'mturk_assignment' not in [f.name for f in model._meta.fields]:
            raise NotImplementedError(
                "Model %s does not have a mturk_assignment field" % model)

        kwargs['out_content_type'] = ContentType.objects.get_for_model(model)
        del kwargs['out_content_type_model']

    if 'examples_good' in kwargs:
        example_ids = []
        for obj in kwargs['examples_good']:
            example, _ = experiment.examples.get_or_create(
                content_type=ContentType.objects.get_for_model(obj.__class__),
                object_id=obj.id)
            example_ids.append(example.id)
        ExperimentExample.objects.filter(id__in=example_ids).update(good=True)
        del kwargs['examples_good']

    if 'examples_bad' in kwargs:
        example_ids = []
        for obj in kwargs['examples_bad']:
            example, _ = experiment.examples.get_or_create(
                content_type=ContentType.objects.get_for_model(obj.__class__),
                object_id=obj.id)
            example_ids.append(example.id)
        ExperimentExample.objects.filter(id__in=example_ids).update(good=False)
        del kwargs['examples_bad']

    if 'test_contents' in kwargs:
        for obj in kwargs['test_contents']:
            t, _ = experiment.test_contents.get_or_create(
                content_type=ContentType.objects.get_for_model(obj.__class__),
                object_id=obj.id)
            ExperimentTestContent.objects.filter(id=t.id).update(
                priority=experiment.content_priority(obj))
        del kwargs['test_contents']

    # default parameters
    new_hit_settings = {
        'frame_height': 768,  # almost all workers have a screen height of 768
        'duration': 60 * 60,
        'lifetime': 3600 * 24 * 31,
        'auto_approval_delay': 259200,
        'feedback_bonus': Decimal('0.02'),
        'auto_add_hits': False,
        'max_active_hits': 200,
        'max_total_hits': 100000,
        'out_count_ratio': 1,
        'qualifications': '{ "num_approved": 1000, "perc_approved": 97 }',
        'requirements': '{}',
        'content_filter': '{}',
    }

    if settings.MTURK_SANDBOX:
        new_hit_settings.update({
            'qualifications': '{}',
            'min_output_consensus': 1,
            'duration': 60 * 60 * 24 * 7,
            #'max_active_hits': 50,
        })

    new_hit_settings.update(kwargs)

    if 'min_output_consensus' not in new_hit_settings:
        new_hit_settings['min_output_consensus'] = (
            new_hit_settings['num_outputs_max'])

    # sanity check
    if new_hit_settings['reward'] > Decimal('0.2'):
        raise ValueError("Reward too high")

    experiment.set_new_hit_settings(**new_hit_settings)


def configure_all_experiments(show_progress=False):
    """ Configure all experiments by searching for modules of the form
    '<app>.experiments' (where "app" is an installed app).  The method
    configure_experiment() is then invoked for each such module found. """

    from mturk.models import Experiment
    with transaction.atomic():

        # turn off all experiments unless turned on by configure_experiments
        for exp in Experiment.objects.all():
            if exp.new_hit_settings:
                exp.new_hit_settings.auto_add_hits = False
                exp.new_hit_settings.save()

        from common.utils import import_modules
        modules = import_modules(settings.MTURK_MODULES)
        for mt in modules:
            if show_progress:
                print '    Running %s.configure_experiments()' % mt.__name__
            mt.configure_experiments()
