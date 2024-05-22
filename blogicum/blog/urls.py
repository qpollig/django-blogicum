from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path(
        '',
        views.PostListView.as_view(),
        name='index'
    ),
    path(
        'category/<slug:category_slug>/',
        views.category_posts,
        name='category_posts'
    ),

    path(
        'posts/create/',
        views.CreatePostView.as_view(),
        name='create_post'
    ),
    path(
        'posts/<int:id>/',
        views.PostDetailView.as_view(),
        name='post_detail'
    ),
    path(
        'posts/<int:id>/edit/',
        views.edit_post,
        name='edit_post'
    ),
    path(
        'posts/<int:id>/delete/',
        views.DeletePostView.as_view(),
        name='delete_post'
    ),

    path(
        'posts/<int:post_id>/comment/',
        views.AddCommentView.as_view(),
        name='add_comment'
    ),
    path(
        'posts/<int:post_id>/delete_comment/<int:comment_id>/',
        views.DeleteCommentView.as_view(),
        name='delete_comment'
    ),
    path(
        'posts/<int:post_id>/edit_comment/<int:comment_id>/',
        views.EditCommentView.as_view(),
        name='edit_comment'
    ),

    path(
        'profile/<username>/',
        views.ProfileView.as_view(),
        name='profile'
    ),
    path(
        'profile/edit/<username>/',
        views.EditProfileView.as_view(),
        name='edit_profile'
    ),

]
