from django.conf import settings
from django.shortcuts import render
from django.http import Http404
from django.db.models.loading import get_model

from django.core.cache import get_cache
from cacheback.decorators import cacheback

from common.utils import json_response
from home.tasks import update_index_context_task


# two layers of caching for the home page: database and memcached
@cacheback(3600)
def index_context():
    if settings.ENABLE_CACHING:
        context = get_cache('persistent').get('home.index_context')
    else:
        context = {}
    if not context:
        context = update_index_context_task()
    return context


def index(request):
    return render(request, 'index.html', index_context())


def publications(request, slug='opensurfaces'):
    return render(request, 'publications_%s.html' % slug, {
        'nav': 'publications',
        'subnav': slug,
        'iiw': slug == 'intrinsic',
    })


def entry_ajax(request, app_label, model):
    if app_label not in ('shapes', 'photos'):
        raise Http404

    ids = request.GET['ids'].split('-')
    model = get_model(app_label, model)
    queryset = model.objects.filter(id__in=ids)

    if hasattr(model, 'photo'):
        queryset = queryset.select_related('photo')
    elif hasattr(model, 'shape'):
        queryset = queryset.select_related('shape', 'shape__photo')

    return json_response({
        'objects': {q.id: q.get_entry_dict() for q in queryset.iterator()}
    })


def dump_csv(request, app_label, model):
    from common.utils import dump_model_csv_view
    return dump_model_csv_view(app_label, model)
