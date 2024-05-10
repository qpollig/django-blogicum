from django.conf import settings
from django.shortcuts import get_object_or_404, render

from .models import Category, Post


def index(request):
    template_name = 'blog/index.html'
    post_list = (
        Post
        .published
        .order_by('-pub_date')
        [:settings.POSTS_ON_PAGE]
    )
    context = {
        'post_list': post_list
    }
    return render(request, template_name, context)


def post_detail(request, id):
    template_name = 'blog/detail.html'
    post = get_object_or_404(
        Post.published, pk=id
    )
    context = {
        'post': post,
    }
    return render(request, template_name, context)


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    posts = category.posts(manager='published').all()
    context = {'category': category, 'post_list': posts}
    return render(request, template, context)
