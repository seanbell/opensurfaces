"""
Utilities for using the CUBAM model (python package ``cubam``), as described
in the paper

.. pull-quote::

    Welinder P., Branson S., Belongie S., Perona, P. "The Multidimensional
    Wisdom of Crowds." Conference on Neural Information Processing Systems
    (NIPS) 2010.

"""
# This allows us to ``import cubam`` even though the current module is called
# cubam
from __future__ import absolute_import

import os
import tempfile
from collections import namedtuple
from clint.textui import progress

from django.db import models, transaction
from django.db.models.query import QuerySet
from mturk.models import Experiment


def update_votes_cubam(
        object_model, labels, object_attr, label_attr,
        object_label_attr, user_attr='user_id',
        quality_method_attr='quality_method', score_threshold=0,
        min_votes=4, show_progress=False, return_changed_objects=False,
        experiment_filter=None):
    """
    Updates all binary labels for an object model (``object_model``) using the
    CUBAM model from:

    .. pull-quote::

        Welinder P., Branson S., Belongie S., Perona, P. "The Multidimensional
        Wisdom of Crowds." Conference on Neural Information Processing Systems
        (NIPS) 2010.

    :param object_model: django model for objects being labeled
    :type object_model: ``django.db.models.Model``

    :param labels: list of labels.  Each item in the list is expected to be an
        object ``x`` such that ``getattr(x, label_attr)`` is the Boolean label to be used.
    :type labels: ``models.Model`` or ``django.db.models.query.QuerySet`` or ``list``

    :param object_attr: name of the object id on each label.  So, for each label ``x``,
        ``getattr(x, object_attr)`` should give the object that the label is describing.

    :param label_attr: name of the label attribute (e.g. ``'correct'`` or ``'flat'``)

    :param object_label_attr: name of the aggregated attribute on the object
        (e.g. ``'scene_quality_correct'``).  **Note**: ``object_label_attr + '_score'``
        is also set to be the CUBAM score.

    :param user_attr: (default: ``'user_id'``) name of the user attribute on
        the label.  So, for each label ``x``, ``getattr(x, user_attr)`` should give
        the user that provided that label.

    :param quality_method_attr: (default ``'quality_method'``) name of the
        attribute on the label that records which method set the label.  If not
        ``None``, this attribute is set to ``'C'``.

    :param score_threshold: threshold for CUBAM scores where a label is
        considered ``True``.

    :param min_votes: objects with fewer than this many votes are not updated.

    :param show_progress: if ``True``, render progress bars during the operation.

    :param return_changed_objects: if ``True``, return a list of objects that
        were updated.

    :param experiment_filter: if specified, the filter to obtain the
        experiments that this label was obtained from.  Typically the filter is
        ``{'slug': '<your_slug>'}``.  This is used to check whether anything new
        was submitted since the last time this was run.  If nothing changed, this
        funciton returns without updating.

    :return: the changed objects if ``return_changed_objects=True``, else ``None``
    :rtype: ``list`` or ``None``

    """

    if experiment_filter:
        experiment_qset = Experiment.objects.filter(**experiment_filter)
        if not experiment_qset.exists():
            print "WARNING: No experiments found with filter %s" % experiment_filter
            return []
        dirty = experiment_qset.filter(cubam_dirty=True).exists()
    else:
        dirty = True

    if dirty:
        print "Experiment (%s): cubam_dirty=True" % experiment_filter
    else:
        print "Experiment (%s): cubam_dirty=False: not running update_votes_cubam" % experiment_filter
        return []

    try:
        if experiment_filter:
            experiment_qset.update(cubam_dirty=False)
        return _update_votes_cubam_impl(
            object_model=object_model,
            labels=labels,
            object_attr=object_attr,
            label_attr=label_attr,
            object_label_attr=object_label_attr,
            user_attr=user_attr,
            quality_method_attr=quality_method_attr,
            score_threshold=score_threshold,
            min_votes=min_votes,
            show_progress=show_progress,
            return_changed_objects=return_changed_objects
        )
    except:
        if experiment_filter:
            experiment_qset.update(cubam_dirty=True)
        raise


def _update_votes_cubam_impl(
        object_model, labels, object_attr, label_attr,
        object_label_attr, user_attr='user_id',
        quality_method_attr='quality_method', score_threshold=0,
        min_votes=5, show_progress=False, return_changed_objects=False):

    if return_changed_objects:
        changed_object_ids = []

    print '\nStarting update_votes_cubam(%s, <QuerySet>, %s, %s, %s, %s)' % (
        object_model, object_attr, label_attr, object_label_attr, user_attr
    )
    print 'Gathering labels (%s: %s)...' % (object_model, object_label_attr)
    processed_labels, vote_counts = _prepare_cubam_labels(
        labels, object_attr, user_attr, label_attr)

    if len(processed_labels) < max(1, min_votes):
        print 'Not enough labels (%s labels)' % len(processed_labels)
        return []

    print 'Computing scores... (%s labels, %s objects)' % (
        len(processed_labels), len(vote_counts))
    cubam_scores = compute_cubam_1d_signal_model_scores(processed_labels)

    # keep track of changes
    label_matrix = [[0, 0], [0, 0]]
    label_matrix_none = [0, 0]
    label_total = 0

    print 'Storing new labels (%s.%s)...' % (object_model, object_label_attr)
    object_ids = [id for id in vote_counts if vote_counts[id] >= min_votes]
    iterator = progress.bar(object_ids) if show_progress else object_ids

    # commit every 1000 updates: batch for speed, but without holding too many
    # modified objects at once.
    count = 0
    with transaction.commit_manually():
        for id in iterator:
            # fetch old labels one at a time (doing this in a giant single
            # query didn't work well; it took forever and couldn't be cancelled)
            if quality_method_attr:
                old_label, quality_method = object_model.objects.filter(id=id) \
                    .values_list(object_label_attr, quality_method_attr).get()
                # important to skip admin-set labels, or else we overwrite
                # manual changes to the database.
                if quality_method == 'A':
                    continue
            else:
                old_label = object_model.objects.filter(id=id) \
                    .values_list(object_label_attr, flat=True).get()

            # threshold new label and record what changed
            label = bool(float(cubam_scores[id]) > score_threshold)
            score = cubam_scores[id]

            if old_label is None:
                label_matrix_none[label] += 1
            else:
                label_matrix[bool(old_label)][label] += 1
            label_total += 1

            # store new label
            d = {
                object_label_attr: label,
                object_label_attr + '_score': score,
            }
            if quality_method_attr:
                d[quality_method_attr] = 'C'
            object_model.objects.filter(id=id).update(**d)

            if return_changed_objects and (old_label is None or old_label != label):
                changed_object_ids.append(id)

            count += 1
            if count >= 1000:
                transaction.commit()
                count = 0
        transaction.commit()

    print '%s: %s: None --> false: %d, None --> true: %d, true --> false: %d, false --> true: %d, total: %d' % (
        object_model, object_label_attr,
        label_matrix_none[0], label_matrix_none[1],
        label_matrix[1][0], label_matrix[0][1],
        label_total)

    if return_changed_objects:
        print 'Fetching changed objects...'
        ret = object_model.objects.in_bulk(changed_object_ids).values()
    else:
        ret = None

    print 'Done update_votes_cubam.'
    return ret


def _prepare_cubam_labels(input_labels, object_attr, user_attr, label_attr):
    """ Helper to prepare CUBAM labels """

    # convert to a list
    if isinstance(input_labels, (list, tuple)):
        objects = [
            (getattr(o, object_attr), getattr(o, user_attr), getattr(o, label_attr))
            for o in input_labels
        ]
    else:
        # grab all objects at once
        if isinstance(input_labels, models.Model):
            input_labels = input_labels.objects.all()
        elif not isinstance(input_labels, QuerySet):
            raise ValueError('input_labels is not a list, Queryset, or Model')
        objects = input_labels.order_by().values_list(
            object_attr, user_attr, label_attr)

    output_labels = []

    # repack into vote counts
    vote_counts = {}
    for (object_id, user_id, label) in objects:
        output_labels.append({
            'object_id': object_id,
            'user_id': user_id,
            'label': label,
        })
        if object_id in vote_counts:
            vote_counts[object_id] += 1
        else:
            vote_counts[object_id] = 1

    return (output_labels, vote_counts)


def compute_cubam_1d_signal_model_scores(labels):
    """
    Takes an array of labels with multiple votes per object, and computes a
    score of how likely each object is to be 1.  It runs the 1d Binary Signal
    Model described in:

    .. pull-quote::

        Welinder P., Branson S., Belongie S., Perona, P. "The Multidimensional
        Wisdom of Crowds." Conference on Neural Information Processing Systems
        (NIPS) 2010.

    :param labels: array of tuples ``(object_id, user_id, label)``

    :return: Dictionary mapping ``{object_id: score}``.  The more positive the
        score, the more likely it is to be a 1.  To minimize the error rate,
        threshold at 0.  To avoid false positives, threshold at a higher value.

    :rtype: ``dict``
    """

    # convert to named tuples
    CubamLabel = namedtuple('CubamLabel', 'object_id user_id label')
    labels = [CubamLabel(**l) for l in labels]

    # map original id --> normalized id
    usr_map = {}
    obj_map = {}
    for l in labels:
        if l.user_id not in usr_map:
            usr_map[l.user_id] = len(usr_map)
        if l.object_id not in obj_map:
            obj_map[l.object_id] = len(obj_map)

    # write to temporary file
    fd, fname = tempfile.mkstemp(text=True)

    # save to CUBAM format
    f = os.fdopen(fd, 'w')
    f.write('%d %d %d\n' % (len(obj_map), len(usr_map), len(labels)))
    for l in labels:
        f.write('%d %d %d\n' % (
            obj_map[l.object_id], usr_map[l.user_id], int(l.label)))
    f.close()

    try:
        # run model
        # Note: the import has to be here or else the webserver won't start and no
        # error message will be given :(
        from cubam import Binary1dSignalModel
        m = Binary1dSignalModel(filename=fname)
        m.optimize_param()
        image_param = m.get_image_param()

        # Note: there seems to be some problems with m.__del__() getting called
        # after the C++ library is already partially garbage collected, so clean up
        # the model here:
        del m
    finally:
        os.remove(fname)

    # unmap ids
    obj_unmap = {v: k for k, v in obj_map.iteritems()}
    return {obj_unmap[id]: image_param[id][0] for id in xrange(len(obj_map))}


#def update_categories_cubam(
    #object_model, label_queryset, object_attr, label_attr, object_label_attr,
    #object_score_attr, user_attr='user_id', score_threshold=0, min_votes=4,
    #show_progress=False, return_changed_objects=False):

    #"""
    #Updates all labels for an object using the model from:

    #Welinder P., Branson S., Belongie S., Perona, P. "The Multidimensional
    #Wisdom of Crowds." Conference on Neural Information Processing Systems
    #(NIPS) 2010.

    #The labels are assumed to be discrete categories.

    #object_model: django model for objects being labeled
    #vote_model: django model for category objects
    #object_attr: name of the object id on the vote (e.g. 'shape_id')
    #label_attr: name of the label attribute (e.g. 'category_id')
    #object_label_attr: name of the aggregated attribute on the object (e.g. 'name')
    #object_score_attr: name of the CUBAM on the object (e.g. 'name_score')
    #user_attr: name of the user attribute on the label (default: 'user')
    #"""

    #if return_changed_objects:
        #changed_object_ids = []

    #with transaction.atomic():
        #print 'Gathering category labels...'
        #labels, vote_counts = _prepare_cubam_labels(
            #label_queryset, object_attr, user_attr, label_attr,
            #show_progress=show_progress)

        #objects = set([l['object_id'] for l in labels])
        #categories = set([l['label'] for l in labels])

        #object_cat_scores = {}
        #for id in objects:
            #object_cat_scores[id] = {}

        #print 'Computing scores...'
        #iterator = categories
        #if show_progress:
            #iterator = progress.bar(categories)
        #for category in iterator:
            #cat_labels = [{
                #'user_id': l['user_id'],
                #'object_id': l['object_id'],
                #'label': (l['label'] == category),
            #} for l in labels]
            #cubam_scores = compute_cubam_1d_signal_model_scores(cat_labels)
            #count = 0
            #for id in cubam_scores:
                #object_cat_scores[id][category] = cubam_scores[id]
                #if cubam_scores[id] > score_threshold:
                    #count += 1
            #print 'category %d: %d scores > %s' % (category, count, score_threshold)

        #num_tf = 0
        #num_ft = 0

        #print 'storing result (%s)...' % object_model

        #object_labels = object_model.objects \
                #.filter(id__in=[id for id in vote_counts
                                #if vote_counts[id] >= min_votes]) \
                #.values_list('id', object_label_attr)

        #iterator = progress.bar(object_labels) if show_progress else object_labels
        #for (id, old_category) in iterator:
            #best_category, best_score = dict_max_value(object_cat_scores[id])
            #if best_score < score_threshold:
                #best_category = none

            #object_model.objects.filter(id=id).update(**{
                #object_label_attr: best_category,
                #object_score_attr: best_score
            #})

            #if old_category != best_category:
                #if old_category is not none and best_category is none:
                    #num_tf += 1
                #elif old_category is none and best_category is not none:
                    #num_ft += 1
                #if return_changed_objects:
                    #changed_object_ids.append(id)

    #print '%s: category --> none: %d, none --> category: %d, total: %d' % (
        #object_model, num_tf, num_ft, len(objects))
    #print 'done.'

    #if return_changed_objects:
        #return object_model.objects.in_bulk(changed_object_ids).values()
    #else:
        #return none
