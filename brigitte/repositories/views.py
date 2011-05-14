from django.http import Http404, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.utils import simplejson
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.template.defaultfilters import slugify, timesince

from brigitte.repositories.decorators import repository_view
from brigitte.repositories.models import Repository
from brigitte.repositories.forms import RepositoryForm, RepositoryUserFormSet, RepositoryDeleteForm
from brigitte.repositories.utils import pygmentize, build_path_breadcrumb
from brigitte.repositories.utils import register_repository_update

# FIXME !!
from django.views.decorators.csrf import csrf_exempt

@login_required
def repositories_manage_list(request):
    return render(request, 'repositories/repository_manage_list.html', {
        'repository_list': Repository.objects.manageable_repositories(
            request.user),
    })

@login_required
def repositories_user(request, user):
    user = get_object_or_404(User, username=user)
    return render(request, 'repositories/repository_user.html', {
        'user': user,
        'repository_list': user.repository_set.public_repositories(),
    })


@login_required
@repository_view(can_admin=True)
def repositories_manage_delete(request, repo):

    if request.method == 'POST':
        delete_form = RepositoryDeleteForm(request.POST)
        if delete_form.is_valid():
            register_repository_update(repo.user, 'deleted', repo)
            messages.success(request, _('Repository deleted.'))
            repo.delete()
            return redirect('repositories_manage_list')
        else:
            raise Http404

# FIXME !!
@csrf_exempt
@login_required
@repository_view(can_admin=True)
def repositories_manage_change(request, repo):
    if request.method == 'POST':
        if request.POST.get('method', None) == 'add_repouser':
            result = False
            error_msg = 'No error message'

            try:
                user = User.objects.get(email=request.POST.get('email', None))
                if repo.user == user:
                    error_msg = 'You cannot re-add the repository owner.'
                elif user.repositoryuser_set.filter(repo=repo).exists():
                    error_msg = 'User already added to repository'
                else:
                    repo.repositoryuser_set.create(user=user)
                    register_repository_update(user, 'changed', repo)
                    result = True
            except User.DoesNotExist:
                error_msg ='Invalid email address'

            return HttpResponse('{"result": "%s", "error_msg": "%s"}' % (
                int(result), error_msg)
            )

        repo_form = RepositoryForm(
            request.user, request.POST, instance=repo, prefix='repository')
        users_formset = RepositoryUserFormSet(request.POST, prefix='users')

        if repo_form.is_valid():
            repo_form.save()

            if users_formset.is_valid():
                for instance in users_formset.save(commit=False):
                    if not instance.pk:
                        instance.repo = repo
                    instance.save()

            register_repository_update(request.user, 'changed', repo)
            messages.success(request, _('Repository updated.'))
            return redirect('repositories_manage_list')
    else:
        repo_form = RepositoryForm(request.user, instance=repo, prefix='repository')
        users_formset = RepositoryUserFormSet(
            prefix='users',
            queryset=repo.alterable_users
        )

    return render(request, 'repositories/repository_manage_change.html', {
        'repo': repo,
        'form': repo_form,
        'delete_form': RepositoryDeleteForm(),
        'users': users_formset,
    })

@login_required
def repositories_manage_add(request):
    if request.method == 'POST':
        form = RepositoryForm(request.user, request.POST)
        if form.is_valid():
            repo = form.save(commit=False)
            repo.user = request.user
            repo.slug = slugify(repo.title)
            repo.save()
            repo.repositoryuser_set.create(
                user=request.user,
                can_read=True,
                can_write=True,
                can_admin=True
            )
            register_repository_update(request.user, 'created', repo)
            messages.success(request, _('Repository added.'))
            return redirect('repositories_manage_list')
    else:
        form = RepositoryForm(request.user)

    return render(request, 'repositories/repository_manage_add.html', {
        'form': form,
    })

def repositories_list(request):
    return render(request, 'repositories/repository_list.html', {
        'repository_list': Repository.objects.public_repositories(),
    })

@repository_view()
def repositories_summary(request, repo):
    return render(request, 'repositories/repository_summary.html', {
        'repository': repo,
    })


@repository_view()
def repositories_commits(request, repo, branchtag):
    count = 10
    page = int(request.GET.get('page', 1))
    skip = (page * count) - count
    if skip < 0:
        skip = 0
    commits = repo.get_commits(count=count, skip=skip, head=branchtag)
    return render(request, 'repositories/repository_commits.html', {
        'repository': repo,
        'commits': commits,
        'branchtag': branchtag,
        'next_page': page + 1,
        'prev_page': page - 1,
    })

@repository_view()
def repositories_commit(request, repo, sha):
    commit = repo.get_commit(sha)

    if not commit:
        raise Http404

    return render(request, 'repositories/repository_commit.html', {
        'repository': repo,
        'commit': commit,
    })

@repository_view()
def repositories_commit_archive(request, repo, sha):
    commit = repo.get_commit(sha)

    try:
        archive = commit.get_archive()
        response = HttpResponse(archive['data'].getvalue(),
            mimetype=archive['mime'])
        response['Content-Disposition'] = \
            'attachment; filename="%s-%s.zip"' \
                % (repo.slug, archive['filename'])
        return response
    except:
        raise Http404

@repository_view()
def repositories_commit_tree(request, repo, sha, path=None):
    commit = repo.get_commit(sha)

    if not commit:
        raise Http404

    if not path or path[-1] == '/':
        if request.is_ajax() and 'commits' in request.GET:
            tree = commit.get_tree(path, commits=True).tree
            tree_elements = []
            for entry in tree:
                tree_elements.append({
                    'tree_id': entry['sha'],
                    'id': entry['commit'].id,
                    'author': entry['commit'].author,
                    'commit_date': entry['commit'].commit_date,
                    'since': timesince(entry['commit'].commit_date),
                })
            return HttpResponse(simplejson.dumps(tree_elements,
                cls=DjangoJSONEncoder), mimetype='application/json')

        tree = commit.get_tree(path)
        if tree is None:
            raise Http404

        return render(request, 'repositories/repository_tree.html', {
            'repository': repo,
            'commit': commit,
            'tree': tree,
            'breadcrumb': build_path_breadcrumb(path)
        })

    else:
        file_obj = commit.get_file(path)
        if file_obj is None:
            raise Http404

        file_blob_pygmentized = pygmentize(
            path.rsplit('.', 1)[-1], file_obj.content)

        return render(request, 'repositories/repository_file.html', {
            'repository': repo,
            'commit': commit,
            'file_path': path,
            'file_obj': file_obj,
            'file_lines': range(1, file_obj.content.count('\n') + 1),
            'file_blob_pygmentized': file_blob_pygmentized,
            'breadcrumb': build_path_breadcrumb(path)
        })

