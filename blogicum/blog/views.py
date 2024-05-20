from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  TemplateView, UpdateView)

from .forms import CommentForm, PostForm
from .models import Category, Comment, Post, User


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


def profile(request, username):
    profile = get_object_or_404(User, username=username)
    page_obj = Post.published.filter(author=profile.id)
    return render(request, 'blog/profile.html', {'profile': profile, 'page_obj': page_obj})


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'user.html', {'form': form})


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:post_detail', id=post.id)
    else:
        form = PostForm()
        context = {'form': form}
        return render(request, 'blog/create.html', context)


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
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all().order_by('-created_at')
        context['form'] = CommentForm()
        return context


def delete_post(request, id):
    template_name = 'blog/create.html'
    instance = get_object_or_404(Post, id=id)
    form = PostForm(instance=instance)
    context = {'form': form}
    if request.method == 'POST':
        instance.delete()
        return redirect('blog:index')
    return render(request, template_name, context)


def edit_post(request, id):
    post = get_object_or_404(Post, id=id)
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
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=post_id)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'blog/comment.html', {'form': form, 'comment': comment})


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
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
    ordering = ['-pub_date']
    paginate_by = settings.POSTS_ON_PAGE


def category_posts(request, category_slug):
    category = Category.objects.get(slug=category_slug)
    posts = Post.published.filter(category=category)

    paginator = Paginator(posts, settings.POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return render(request, 'blog/category.html', {'category': category, 'page_obj': page_obj})
