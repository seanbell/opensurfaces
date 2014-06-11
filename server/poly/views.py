from django.shortcuts import render


def poly_spec(request):
    return render(request, 'poly/spec.html', {})
