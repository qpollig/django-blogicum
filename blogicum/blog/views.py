from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView

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


def delete_post(request, id):
    template_name = 'blog/create.html'
    instance = get_object_or_404(Post, id=id)
    if instance.author != request.user:
        return redirect('blog:post_detail', id=instance.id)
    form = PostForm(instance=instance)
    context = {'form': form}
    if request.method == 'POST':
        with transaction.atomic():
            instance.comments.all().delete()
            instance.delete()
        return redirect('blog:index')
    return render(request, template_name, context)


@login_required
def edit_post(request, id):
    post = get_object_or_404(Post, id=id)
    if post.author != request.user:
        return redirect('blog:post_detail', id=post.id)
    template_name = 'blog/create.html'
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', id=post.id)
    return render(request, template_name, {'form': form})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    template_name = 'include/comments.html'
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.is_published = True
            comment.save()
            return redirect('blog:post_detail', id=post.id)
    else:
        form = CommentForm()
    return render(request, template_name, {'form': form})


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author != request.user:
        return HttpResponseForbidden(
            "Вы не можете редактировать этот комментарий."
        )

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=post_id)
    else:
        form = CommentForm(instance=comment)

    return render(
        request,
        'blog/comment.html',
        {'form': form, 'comment': comment}
    )


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author != request.user:
        return HttpResponseForbidden("Вы не можете удалить этот комментарий.")

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', id=post_id)

    return render(request, 'blog/comment.html', {'comment': comment})


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


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    posts = Post.published.filter(category=category).order_by('-pub_date')

    paginator = Paginator(posts, settings.POSTS_ON_PAGE)
    page_number = (request.
                   GET.get('page'))
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = (paginator.
                    page(paginator.num_pages))

    return render(
        request,
        'blog/category.html',
        {'category': category, 'page_obj': page_obj}
    )
