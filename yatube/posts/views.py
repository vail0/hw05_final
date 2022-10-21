from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def paginate(req, pag_post):
    paginator = Paginator(pag_post, settings.AMOUNT_OF_POSTS)
    page_number = req.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj


@cache_page(20, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    posts = Post.objects.select_related('group', 'author')

    page_obj = paginate(request, posts)

    context = {
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')

    page_obj = paginate(request, posts)

    template = 'posts/group_list.html'
    context = {
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_auth = author.posts.select_related('group')

    following = None
    following = (request.user.is_authenticated
                 and Follow.objects.filter(author=author).exists())

    page_obj = paginate(request, posts_auth)

    context = {
        'author': author,
        'posts_auth': posts_auth,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):

    post = get_object_or_404(Post, pk=post_id)

    comments = post.comments.all()
    form = CommentForm()

    context = {
        'post': post,
        'posts_by': post.author.posts.all(),
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )

    if form.is_valid():
        post = form.save(commit=False)

        post.author = request.user
        post.save()

        return redirect('posts:profile', post.author.username)

    return render(request, 'posts/create_post.html', {'form': form,
                  'is_edit': False})


@login_required
def post_edit(request, post_id):

    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('posts:index', post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)

    return render(request, 'posts/create_post.html',
                  {'form': form, 'is_edit': True, 'post': post})


@login_required
def add_comment(request, post_id):
    # Получите пост
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts_follow = Post.objects.filter(
        author__following__user=request.user)

    page_obj = paginate(request, posts_follow)

    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    Follow.objects.filter(user=request.user,
                          author__username=username).delete()

    return redirect('posts:profile', username)
