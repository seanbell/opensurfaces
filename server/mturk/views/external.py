"""
Tasks viewed from the mturk website nested in an iframe
"""

import json
import random
import datetime
from ua_parser import user_agent_parser

from django.conf import settings
from django.core.context_processors import csrf
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import never_cache

from common.utils import recursive_sum, recursive_dict_exclude, \
    html_error_response

from mturk.models import MtHit, MtAssignment, Experiment, ExperimentWorker
from mturk.tasks import mturk_submit_task, \
    increment_hit_counter_task, expire_hit_task

from mturk.utils import get_or_create_mturk_worker_from_request, \
    get_content_model_prefetch, fetch_hit_contents, \
    fetch_content_tuples
from common.utils import json_success_response, json_error_response


#
# View functions
#


#@staff_member_required
@never_cache
def admin_preview_task(request, experiment_id, override, hit_id=None):
    if hit_id:
        hit = get_object_or_404(MtHit, id=hit_id)
    else:
        hits = MtHit.objects \
            .filter(hit_type__experiment_id=experiment_id, ) \
            .order_by('-num_assignments_completed', '?')[:1]
        try:
            hit = hits[0]
        except:
            try:
                e = Experiment.objects.get(id=experiment_id)
                return html_error_response(
                    request, 'There are no HITs created for this experiment yet.  '
                    'Experiment id: %s, slug: "%s", title: "%s".' % (
                        e.id, e.slug, e.new_hit_settings.title)
                )
            except:
                return html_error_response(
                    request, 'This experiment does not exist.  Experiment id: %s.' %
                    (experiment_id)
                )

    return external_task(
        request, experiment_id=experiment_id, hit=hit, override=override)


@require_POST
def external_incompatible(request, id):
    """ Increment view counter for an incompatible view """
    increment_hit_counter_task.delay(id, 'incompatible_count')
    return json_success_response()


@require_POST
def external_compatible(request, id):
    """ Increment view counter for a compatible view """
    increment_hit_counter_task.delay(id, 'compatible_count')
    return json_success_response()


@ensure_csrf_cookie
#@transaction.atomic  <-- already provieded by ATOMIC_REQUESTS
def external_task(request, experiment_id, hit=None, override=None):
    """
    Renders a MTurk task, both preview and instructions.
    override: either None, "inst", "task", or "tut"
    """

    # override is only for staff members
    #if not request.user.is_staff:
        #override = None

    # browser check
    response = external_task_browser_check(request)
    if response:
        return response

    # get HIT info etc
    context_or_response = external_task_prepare_context(
        request, experiment_id, hit, override)
    if not isinstance(context_or_response, dict):
        return context_or_response
    else:
        context = context_or_response

    # handle tutorials: both GET and POST.  if this returns None, then we know
    # this is not a tutorial (or tutorial submission)
    response = external_task_tutorial(request, context)
    if response:
        return response

    # either task or instructions page
    if request.method == 'POST':
        return external_task_POST(request, context)
    else:
        return external_task_GET(request, context)


#
# Helper functions
#


def is_preview_request(request):
    """ Return true if this is a request for a task preview """
    return ('assignmentId' not in request.GET or
            request.GET['assignmentId'] == 'ASSIGNMENT_ID_NOT_AVAILABLE')


def external_task_browser_check(request):
    if request.method == "GET":
        valid_browser = False
        if 'HTTP_USER_AGENT' in request.META:
            ua = user_agent_parser.Parse(request.META['HTTP_USER_AGENT'])
            if ua['user_agent']['family'].lower() in ('firefox', 'chrome'):
                device = ua['device']
                if 'is_mobile' not in device or not device['is_mobile']:
                    valid_browser = True
        if not valid_browser:
            return html_error_response(
                request, '''
                This task requires Google Chrome. <br/><br/>
                <a class="btn" href="http://www.google.com/chrome/"
                target="_blank">Get Google Chrome</a>
            ''')
    return None


def external_task_prepare_context(request, experiment_id, hit, override):
    """ Fetch hit, experiment, assignment, worker, etc.  Returns either a
    dictionary on success, or a response (or exception) if there is some error.
    """

    # obtain HIT
    if hit is None:
        if 'hitId' not in request.GET:
            if request.user.is_staff:
                return html_error_response(
                    request, 'HIT ID missing from GET parameters')
            else:
                raise Http404

        hit_id = request.GET['hitId']
        try:
            hit = MtHit.objects \
                .select_related(
                    'hit_type__experiment',
                    'hit_type__experiment_settings',
                    'hit_type__requirements') \
                .get(id=hit_id)
        except MtHit.DoesNotExist:
            # if this HIT cannot be found, tell Amazon about it
            if (override is None and
                    not request.user.is_staff and
                    'assignmentId' in request.GET and
                    'workerId' in request.GET and
                    'turkSubmitTo' in request.GET):
                expire_hit_task.delay(hit_id)
            raise Http404

    # obtain experiment
    experiment = hit.hit_type.experiment
    if experiment.id != int(experiment_id):
        if request.user.is_staff:
            return html_error_response(
                request, 'Experiment ID (%s) does not match HIT (%s)' % (
                    experiment_id, experiment.id)
            )
        else:
            raise Http404

    # obtain worker and assignment
    worker = get_or_create_mturk_worker_from_request(request)
    assignment_dirty = False
    if worker and 'assignmentId' in request.GET:
        assignment, _ = MtAssignment.objects.get_or_create(
            id=request.GET['assignmentId'],
            defaults={'hit': hit, 'worker': worker})
        if assignment.hit != hit or assignment.worker != worker:
            assignment.hit = hit
            assignment.worker = worker
            assignment_dirty = True
    else:
        assignment = None
        worker = None

    # obtain worker info specific to the experiment and worker
    if experiment and worker:
        experiment_worker, _ = ExperimentWorker.objects.get_or_create(
            experiment=experiment, worker=worker)
    else:
        experiment_worker = None

    # don't let blocked workers perform our tasks
    if (worker and worker.blocked) or (experiment_worker and experiment_worker.blocked):
        message = "Your submissions are too low quality.  Please stop doing our tasks."
        if experiment_worker and experiment_worker.blocked_reason:
            message += "<br/><br/>" + experiment_worker.blocked_reason
        elif worker and worker.blocked_reason:
            message += "<br/><br/>" + worker.blocked_reason
        return html_error_response(request, message)

    # fetch contents
    hit_contents = fetch_hit_contents(hit)
    if override and 'publishable' in request.GET:
        hit_contents = filter(lambda x: x and x.publishable(), hit_contents)
    if not hit.num_contents or not hit_contents:
        # (in the if statement, also test hit.num_contents since it is only set
        # after the last content is added)
        return html_error_response(
            request, "Somehow there are no items in this HIT.")

    # fetch test (sentinel) contents
    if experiment_worker:
        if assignment.num_test_contents is None:
            n = experiment.test_contents_per_assignment
            if n > 0:
                # select new test contents from the set of possible contents
                # (that the user has not already answered)
                test_content_wrappers = experiment.test_contents.all() \
                    .exclude(responses__experiment_worker=experiment_worker) \
                    .order_by('-priority')[:n]

                # register chosen items with assignment
                assignment.test_contents.add(*test_content_wrappers)
            else:
                test_content_wrappers = []

            assignment.num_test_contents = len(test_content_wrappers)
            assignment_dirty = True
        elif assignment.num_test_contents > 0:
            # re-fetch existing contents
            test_content_wrappers = assignment.test_contents.all()
        else:
            test_content_wrappers = []

        # fetch objects from inside the wrappers
        if test_content_wrappers:
            test_contents = fetch_content_tuples([
                (x.content_type_id, x.object_id)
                for x in test_content_wrappers
            ])
        else:
            test_contents = []
    else:
        test_contents = []
        test_content_wrappers = []

    # shuffle together (some tasks may sort contents again in javascript)
    contents = hit_contents + test_contents
    random.shuffle(contents)

    # prepare context data
    context = {
        'hit': hit,
        'assignment': assignment,
        'worker': worker,
        'experiment': experiment,
        'experiment_id': experiment_id,
        'experiment_worker': experiment_worker,
        'slug': experiment.slug,
        'hit_contents': hit_contents,
        'test_content_wrappers': test_content_wrappers,
        'test_contents': test_contents,
        'contents': contents,
        'num_contents': len(contents),
        'num_contents_predicted': (len(hit_contents) +
                                   experiment.test_contents_per_assignment),
        'override': override,
    }
    if len(contents) == 1:
        context['content'] = contents[0]

    if experiment.version >= 2:
        # old experiments (version 1) don't use this
        context['contents_json'] = json.dumps(
            [c.get_entry_dict() for c in contents])

    # list of ids as json
    context['content_id_json'] = json.dumps(
        [{'id': c.id} for c in contents])

    # requirements
    for req in hit.hit_type.requirements.values('name', 'value'):
        context[req['name']] = req['value']

    if assignment_dirty:
        assignment.save()

    return context


def external_task_tutorial(request, context):
    """ Handle tutorials.  On a GET, decide whether to serve up a tutorial.
    On a POST, record that the tutorial was completed, then the client will
    refresh.  Returns either a response or None. """

    # unpack some variables
    experiment, worker, override = [
        context[k] for k in ['experiment', 'worker', 'override']]

    if (request.method == "GET" and experiment.has_tutorial and
            (override == "tut" or not is_preview_request(request))):

        show_tutorial = (override == "tut" or
                         not context['experiment_worker'].tutorial_completed)
        if show_tutorial:
            context.update(csrf(request))
            template_name = experiment.template_name()
            return render(request, '%s_tut.html' % template_name, context)

    elif (request.method == "POST" and override is None and
          'tutorial_complete' in request.POST and
          request.POST['tutorial_complete'] == 'true'):

        ew_id = context['experiment_worker'].id
        ExperimentWorker.objects.filter(id=ew_id) \
            .update(tutorial_completed=True)
        return json_success_response()

    return None


def external_task_POST(request, context):
    """ Handles POSTs for mturk tasks.  Returns a response. """

    # unpack some variables
    experiment, hit, assignment, worker, override, experiment_worker = [
        context[k] for k in [
            'experiment', 'hit', 'assignment', 'worker', 'override',
            'experiment_worker'
        ]
    ]

    # error checks
    if override is not None:
        return json_error_response(
            "You cannot submit in admin preview mode.")
    if not worker or not assignment:
        return json_error_response(
            "There was an error obtaining your Assignment ID from Amazon.")

    # check that POST is allowed
    if hit.sandbox and not settings.MTURK_ACCEPT_SANDBOX_HITS:
        return json_error_response(
            "Not currently accepting sandbox HITs.  POST data: " +
            json.dumps(request.POST))

    # extract submit data
    results = json.loads(request.POST['results'])
    time_ms = json.loads(request.POST['time_ms']) \
        if 'time_ms' in request.POST else None
    time_active_ms = json.loads(request.POST['time_active_ms']) \
        if 'time_active_ms' in request.POST else None
    time_load_ms = json.loads(request.POST['time_load_ms']) \
        if 'time_load_ms' in request.POST else None
    complete = ('partial' not in request.POST or
                str(request.POST['partial']) != 'true')
    version = json.loads(request.POST['version'])
    action_log = request.POST.get('action_log', '')
    screen_width = request.POST.get('screen_width', None)
    screen_height = request.POST.get('screen_height', None)

    # fix any potential str/int issues
    if isinstance(time_ms, basestring) and time_ms.isdigit():
        time_ms = int(time_ms)
    if isinstance(time_active_ms, basestring) and time_active_ms.isdigit():
        time_active_ms = int(time_active_ms)
    if isinstance(time_load_ms, basestring) and time_load_ms.isdigit():
        time_load_ms = int(time_load_ms)

    # store assignment POST information
    post_dict = {}
    meta_dict = {}
    for k, v in request.META.iteritems():
        # some non-encodable things get put in here -- filter them out by
        # forcing the unicode encoding
        try:
            meta_dict[unicode(k)] = unicode(v)
        except:
            pass
    for k, v in request.POST.iteritems():
        # some non-encodable things get put in here -- filter them out by
        # forcing the unicode encoding
        try:
            post_dict[unicode(k)] = unicode(v)
        except:
            pass

    # store dictionaries, not nested dictionaries
    post_dict[u'results'] = recursive_dict_exclude(results, [
        u'screenshot'])
    post_dict[u'time_ms'] = time_ms
    post_dict[u'time_active_ms'] = time_active_ms
    post_dict[u'time_load_ms'] = time_load_ms

    assignment.post_data = json.dumps(post_dict)
    assignment.post_meta = json.dumps(meta_dict)
    if 'HTTP_USER_AGENT' in request.META:
        assignment.user_agent = request.META['HTTP_USER_AGENT']

    assignment_dirty = False
    experiment_worker_dirty = False

    # update assignment info
    if complete:
        assignment.time_ms = recursive_sum(time_ms)
        assignment.time_active_ms = recursive_sum(time_active_ms)
        assignment.time_load_ms = recursive_sum(time_load_ms)
        assignment.status = MtAssignment.str_to_status['Submitted']
        assignment.submit_time = datetime.datetime.now()
        assignment.action_log = action_log
        assignment.screen_width = screen_width
        assignment.screen_height = screen_height
        if 'feedback' in request.POST:
            assignment.feedback = request.POST['feedback']
            # must fill in at least 2/3 fields to count
            if assignment.feedback and len(json.loads(assignment.feedback)) >= 2:
                assignment.has_feedback = True
        assignment_dirty = True

    # mark test contents data as seen.  it can't be done async or else the next
    # task will re-serve the same test items.
    rejected_assignment = False
    if assignment.num_test_contents:
        experiment_worker = context['experiment_worker']
        test_content_wrappers = context['test_content_wrappers']
        test_contents = context['test_contents']

        # grade test contents
        responses, responses_correct = hit.hit_type.experiment_settings \
            .out_content_model().mturk_grade_test(
                test_content_wrappers, test_contents, results)

        # store in database
        for i, tcw in enumerate(test_content_wrappers):
            # If the user accepts multiple HITs at once, then they can be
            # served the same test objects.  In that case, only store their
            # first answer, since the second time they see it, they will know
            # it is a test item.
            if not tcw.responses.filter(experiment_worker=experiment_worker).exists():
                tcw.responses.create(
                    experiment_worker=experiment_worker,
                    assignment=assignment,
                    response=unicode(responses[i]),
                    correct=responses_correct[i],
                )

        # update local correct counts
        assignment.num_test_correct = sum(responses_correct)
        assignment.num_test_incorrect = sum(not x for x in responses_correct)
        assignment_dirty = True

        # update global correct counts
        experiment_worker.num_test_correct = \
            experiment_worker.test_content_responses.filter(correct=True).count()
        experiment_worker.num_test_incorrect = \
            experiment_worker.test_content_responses.filter(correct=False).count()
        experiment_worker_dirty = True

        # always approve, but give a message if they do badly
        if assignment.num_test_incorrect >= 3 and assignment.num_test_correct == 0:
            perc = int(100 * assignment.num_test_correct / (
                assignment.num_test_correct + assignment.num_test_incorrect))
            message = make_reject_message(experiment, hit, perc)
            #from mturk.tasks import reject_assignment_task
            from mturk.tasks import approve_assignment_task
            approve_assignment_task.apply_async(
                kwargs={
                    'assignment_id': assignment.id,
                    'feedback': message,
                }, countdown=60, retry=True, retry_policy={'max_retries': 100})
            rejected_assignment = True

    # block if accuracy every creeps below 80% (with at least 5 errors)
    if experiment_worker.num_test_incorrect > 5:
        perc = int(100 * experiment_worker.num_test_correct / (
            experiment_worker.num_test_correct +
            experiment_worker.num_test_incorrect))

        if perc < 80:
            message = make_reject_message(experiment, hit, perc)
            experiment_worker.block(reason=message, method='T', save=False)
            experiment_worker_dirty = True

    # otherwise auto-approve
    elif (not rejected_assignment and
            (experiment_worker.auto_approve or settings.MTURK_AUTO_APPROVE)):
        from mturk.tasks import approve_assignment_task
        approve_assignment_task.apply_async(
            kwargs={
                'assignment_id': assignment.id,
                'feedback': experiment_worker.auto_approve_message,
            }, countdown=60, retry=True, retry_policy={'max_retries': 100})

    if assignment_dirty:
        assignment.save()
    if experiment_worker_dirty:
        experiment_worker.save()

    # submit (rest of) data asynchronously
    mturk_submit_task.apply_async(
        # note: 'contents' not serialized in this list -- the task re-fetches
        # this from the database.
        kwargs={
            'user_id': worker.user_id,
            'mturk_hit_id': hit.id,
            'mturk_assignment_id': assignment.id,
            'experiment_id': experiment.id,
            'results': results,  # dict with content id as key
            'time_ms': time_ms,  # number or dict with content id as key
            'time_active_ms': time_active_ms,  # same format as time_ms
            'time_load_ms': time_load_ms,
            'complete': complete,
            'version': version,
        },
        retry=True,
        retry_policy={
            'max_retries': None,  # (retry forever)
            'interval_start': 300,
            'interval_step': 60,
            'interval_max': 600,
        }
    )

    # success
    return json_success_response()


def make_reject_message(experiment, hit, perc):
    """
    perc: percentage correct, ranging from 0 to 100.
    """
    # make an experiment-specific reject message
    module = experiment.get_module()
    if module and hasattr(module, 'make_reject_message'):
        message = module.make_reject_message(experiment, hit, perc)
    else:
        message = None

    if not message:
        message = (
            "We checked some of your answers against our correct answers "
            "and found that your accuracy was %s percent, which is too "
            "low.  This is for the task: %s."
        ) % (perc, hit.hit_type.title)

    return message


def external_task_GET(request, context):
    """ Handles GETs for mturk tasks.  Returns a response. """

    # unpack some variables
    override, experiment = [context[k] for k in ['override', 'experiment']]

    # template name is based on experiment parameters
    if experiment.variant:
        variant = json.loads(experiment.variant)
    else:
        variant = None
    context['variant'] = variant

    # template names
    template_name = experiment.template_name()
    context['instructions'] = '%s_inst_content.html' % template_name
    context['content_thumb_template'] = '%s_thumb.html' % template_name

    # fetch examples from database
    publishable = override and 'publishable' in request.GET
    external_task_prepare_examples(
        context, experiment, publishable=publishable)

    # add extra context depending on the task
    external_task_extra_context(experiment.slug, context)

    # decide if we need feedback
    external_task_prepare_feedback(request, context)

    if override == "task" or not is_preview_request(request):
        context.update(csrf(request))
        return render(request, '%s.html' % template_name, context)
    else:
        return render(request, '%s_inst.html' % template_name, context)


def external_task_prepare_feedback(request, context):
    """ Sets the necessary feedback variables """

    # unpack some variables
    experiment, hit, worker = [
        context[k] for k in ['experiment', 'hit', 'worker']
    ]

    # ask for feedback if we haven't gotten any yet, and they have
    # completed at least two other HITs
    context['ask_for_feedback'] = 'false'
    context['feedback_bonus'] = 0
    if context['worker'] and context['hit'].hit_type.feedback_bonus is not None:
        hit_count = MtAssignment.objects.filter(
            worker=worker,
            hit__hit_type=hit.hit_type,
        ).count()
        if hit_count == 3 or (hit_count >= 10 and hit_count % 10 == 0):
            feedback_count = MtAssignment.objects.filter(
                worker=worker,
                has_feedback=True,
                hit__hit_type__experiment__completed_id=experiment.completed_id,
            ).count()
            if feedback_count == 0:
                context['ask_for_feedback'] = 'true'
                context['feedback_bonus'] = hit.hit_type.feedback_bonus


def external_task_prepare_examples(
        context, experiment, num_examples=16, publishable=False):
    """ Prepare good/bad examples for display.  publishable: if True, only show
    creative-commons generic photos -- only useful for generating screenshots
    of tasks for publications.  """

    if not experiment.examples.exists():
        return

    # get content model
    content_model = experiment.examples.all()[0].__class__
    prefetch = get_content_model_prefetch(content_model)

    # good examples
    examples_good = [obj.content for obj in experiment.examples
                        .filter(good=True).order_by('?')[:num_examples]
                        .prefetch_related(*prefetch)]

    # try and find matching bad examples
    group_attr = experiment.examples_group_attr
    if (examples_good and content_model and
            group_attr and hasattr(content_model, group_attr)):
        group_id = group_attr + '_id'

        # object ids, matched on group attribute (e.g. 'shape')
        ids = content_model.objects \
            .filter(**{
                group_id + '__in':
                [getattr(c, group_id) for c in examples_good]
            }) \
            .values_list('id', flat=True)

        # fetch matching bad examples
        examples_bad = [x.content for x in experiment.examples
                        .filter(object_id__in=ids, good=False)
                        .prefetch_related(*prefetch)]

        # re-order good examples to put matches first
        examples_bad_dict = {getattr(x, group_id): x for x in examples_bad}
        examples_good.sort(
            key=lambda x: getattr(x, group_id) not in examples_bad_dict)

        # re-order bad examples to match good examples ordering
        examples_bad = []
        for c in examples_good:
            if getattr(c, group_id) in examples_bad_dict:
                examples_bad.append(examples_bad_dict[getattr(c, group_id)])

        # fetch remaining examples
        num_extra = num_examples - len(examples_bad)
        if num_extra > 0:
            new_examples_bad_queryset = experiment.examples \
                .filter(good=False) \
                .exclude(object_id__in=ids) \
                .order_by('?')[:num_extra] \
                .prefetch_related(*prefetch)
            examples_bad += [
                obj.content for obj in new_examples_bad_queryset]
    else:
        examples_bad = [e.content for e in experiment.examples
                        .filter(good=False).order_by('?')[:num_examples]
                        .prefetch_related(*prefetch)]

    if examples_good:
        if publishable:
            examples_good = filter(lambda x: x.publishable(), examples_good)
        context['examples_good'] = examples_good
        context['examples_good_json'] = json.dumps(
            [c.get_entry_dict() for c in examples_good])
    if examples_bad:
        if publishable:
            examples_bad = filter(lambda x: x.publishable(), examples_bad)
        context['examples_bad'] = examples_bad
        context['examples_bad_json'] = json.dumps(
            [c.get_entry_dict() for c in examples_bad])


def external_task_extra_context(slug, context):
    """ Add extra context for each task """

    module = context['experiment'].get_module()
    if module and hasattr(module, 'external_task_extra_context'):
        module.external_task_extra_context(slug, context)
