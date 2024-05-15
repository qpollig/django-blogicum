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
    template_name = 'blog/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = User.objects.get(username=self.request.user.username)
        context['profile'] = profile
        post_list = Post.published.filter(author=profile)
        context['post_list'] = post_list
        return context


class ProfileEditView(OnlyAuthorMixin, UpdateView):
    model = User
    form_class = PostForm
    template_name = 'blog/user.html'


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('blog:user')


def post_detail(request, id):
    template_name = 'blog/post_detail.html'
    post = get_object_or_404(
        Post.published, pk=id
    )
    context = {
        'post': post,
    }
    return render(request, template_name, context)


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


def add_comment(request, id):
    post = get_object_or_404(Post, id=id)
    template_name = 'include/comments.html'
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('post_detail', id=post.id)
    else:
        form = CommentForm()
        return render(request, template_name, {'form': form})


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


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    queryset = Post.published.select_related('author')
    ordering = ['-pub_date']
    paginate_by = settings.POSTS_ON_PAGE


class CategoryListView(ListView):
    model = Category
    template_name = 'blog/category.html'
    context_object_name = 'category'
    paginate_by = 10

    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        category = get_object_or_404(Category, slug=category_slug, is_published=True)
        return category.posts(manager='published').all()


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', pk=pk)
