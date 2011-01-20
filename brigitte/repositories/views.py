from django.shortcuts import render, get_object_or_404

from brigitte.repositories.models import Repository

def repositories_list(request, template_name=''):
    return render(request, 'repositories/repository_list.html', {
        'repository_list': Repository.objects.all(),
    })

def repositories_summary(request, user, slug, template_name=''):
    repo = get_object_or_404(Repository, user__username=user, slug=slug)

    return render(request, 'repositories/repository_summary.html', {
        'repository': repo,
    })

