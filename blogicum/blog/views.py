from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from .forms import CommentForm, PostForm, ProfileForm
from .models import Category, Comment, Post, User


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class ProfileView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    context_object_name = 'page_obj'
    paginate_by = settings.POSTS_ON_PAGE

    def get_queryset(self):
        profile = get_object_or_404(User, username=self.kwargs['username'])
        return Post.objects.filter(author=profile.id).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_object_or_404(User, username=self.kwargs['username'])
        context['profile'] = profile
        return context


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        if self.request.user.is_authenticated:
            return self.request.user
        return None

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        if self.request.user.is_authenticated:
            return reverse_lazy('blog:profile', kwargs={'username': self.request.user.username})
        return reverse_lazy('login')


class CreatePostView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = self.request.user
        post.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={'username': self.request.user.username})


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    pk_url_kwarg = 'id'

    def get_object(self, queryset=None):
        post = get_object_or_404(Post, id=self.kwargs['id'])

        if not (post.is_published and post.category.is_published
                and post.pub_date <= timezone.now()):
            if post.author != self.request.user:
                raise Http404("Страница не найдена")

        return post

    def get_context_data(self, **kwargs):
        context = (super().
                   get_context_data(**kwargs))
        context['comments'] = (self.
                               object.comments.all().
                               order_by('created_at'))
        context['form'] = CommentForm()
        return context


class DeletePostView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'

    def get_object(self):
        return get_object_or_404(Post, id=self.kwargs['id'])

    def get_success_url(self):
        return reverse_lazy('blog:index')

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return redirect('blog:post_detail', id=instance.id)
        with transaction.atomic():
            instance.comments.all().delete()
            instance.delete()
        return redirect(self.get_success_url())


class EditPostView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, id=kwargs['id'])
        if self.request.user.is_authenticated:
            if post.author != request.user:
                return HttpResponseForbidden(
                    "Вы не можете редактировать этот пост."
                )
            return super().dispatch(request, *args, **kwargs)
        return reverse('blog:post_detail', kwargs={'id': self.kwargs['id']})

    def get_object(self, queryset=None):
        return get_object_or_404(Post, id=self.kwargs['id'])

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'id': self.kwargs['id']})


class AddCommentView(CreateView, LoginRequiredMixin):
    model = Comment
    form_class = CommentForm
    template_name = 'include/comments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = get_object_or_404(Post, id=self.kwargs['post_id'])
        return context

    def form_valid(self, form):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        comment = form.save(commit=False)
        comment.post = post
        comment.author = self.request.user
        comment.save()
        return redirect('blog:post_detail', id=post.id)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'id': self.kwargs['post_id']})


class EditCommentView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, id=kwargs['comment_id'])

        if comment.author != request.user:
            return HttpResponseForbidden(
                "Вы не можете редактировать этот комментарий."
            )
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Comment, id=self.kwargs['comment_id'])

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'id': self.kwargs['post_id']})


class DeleteCommentView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    context_object_name = 'comment'

    def get_object(self, queryset=None):
        return get_object_or_404(Comment, id=self.kwargs['comment_id'])

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'id': self.kwargs['post_id']})

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return redirect('blog:post_detail', id=self.kwargs['post_id'])
        instance.delete()
        return redirect(self.get_success_url())


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'pk': self.object.pk})


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    queryset = Post.published.select_related('author')
    ordering = ('-pub_date')
    paginate_by = settings.POSTS_ON_PAGE


class CategoryPostsView(ListView):
    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'page_obj'
    paginate_by = settings.POSTS_ON_PAGE

    def get_queryset(self):
        category = get_object_or_404(Category, slug=self.kwargs['category_slug'], is_published=True)
        return Post.published.filter(category=category).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = get_object_or_404(Category, slug=self.kwargs['category_slug'], is_published=True)
        context['category'] = category
        return context
