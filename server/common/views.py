from django.views.generic import TemplateView


class Handler500(TemplateView):

    template_name = '500.html'

    @classmethod
    def as_error_view(cls):
        v = cls.as_view()

        def view(request):
            r = v(request)
            r.render()
            return r

        return view
