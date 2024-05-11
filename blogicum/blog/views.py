from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  TemplateView, UpdateView)

from .forms import CommentForm, PostForm
from .models import Category, Post, User


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class ProfileView(TemplateView):
    model = User
    template_name = 'blog/profile.html'


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('blog:user')


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author



'''def post_detail(request, id):
    template_name = 'blog/post_detail.html'
    post = get_object_or_404(
        Post.published, pk=id
    )
    context = {
        'post': post,
    }
    return render(request, template_name, context)'''


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'pk': self.object.pk})


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'


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
