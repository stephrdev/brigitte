from django.shortcuts import get_object_or_404

from brigitte.repositories.models import Repository

def repository_view(f, can_admin=False):
    def wrap(request, user, slug, *args, **kwargs):
        qs = Repository.objects.none()

        if request.user.is_authenticated():
            if can_admin:
                qs = Repository.objects.manageable_repositories(request.user)
            else:
                qs = Repository.objects.available_repositories(request.user)
        else:
            if not can_admin:
                qs = Repository.objects.public_repositories()

        repository = get_object_or_404(qs,
                                       user__username=user,
                                       slug=slug)

        return f(request, repository, *args, **kwargs)

    return wrap

