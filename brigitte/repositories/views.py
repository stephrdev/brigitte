from django.template.context import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from brigitte.repositories.models import Repository

def list(request, template_name='repositories/repository_list.html'):
    template_context = {
        'repository_list': Repository.objects.all(),
    }

    return render_to_response(
        template_name,
        template_context,
        RequestContext(request)
    )

def summary(request, slug, template_name='repositories/repository_summary.html'):
    template_context = {
        'repository_summary': get_object_or_404(Repository, slug=slug),
    }

    return render_to_response(
        template_name,
        template_context,
        RequestContext(request)
    )