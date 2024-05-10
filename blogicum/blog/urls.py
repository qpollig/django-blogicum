from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.index, name='index'),
    path('posts/<int:id>/', views.post_detail, name='post_detail'),
    path('category/<slug:category_slug>/', views.category_posts,
         name='category_posts'),
]


handler404 = 'core.views.page_not_found'
handler500 = 'core.views.server_error'
CSRF_FAILURE_VIEW = 'core.views.csrf_failure'
