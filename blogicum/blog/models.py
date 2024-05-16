from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from core.models import PublishedModel

User = get_user_model()


class Category(PublishedModel):
    title = models.CharField(
        'Заголовок',
        max_length=256,
        blank=False
    )
    description = models.TextField(
        verbose_name='Описание',
        blank=False
    )
    slug = models.SlugField(
        'Идентификатор',
        max_length=64,
        unique=True,
        help_text='Идентификатор страницы для URL; '
                  'разрешены символы латиницы, '
                  'цифры, дефис и подчёркивание.'
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title


class Location(PublishedModel):
    name = models.CharField(
        'Название места',
        max_length=256,
        blank=False
    )

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name


class PostQueryset(models.QuerySet):
    def published(self):
        return self.filter(
            is_published=True,
            pub_date__lt=timezone.now(),
            category__is_published=True
        ).select_related('author', 'category', 'location')


class PublishedPostManager(models.Manager):
    def get_queryset(self):
        return PostQueryset(self.model, using=self._db).published()


class Post(PublishedModel):
    objects = PostQueryset.as_manager()
    published = PublishedPostManager()
    title = models.CharField(
        'Заголовок',
        max_length=256,
        blank=False
    )
    text = models.TextField('Текст', blank=False)
    image = models.ImageField('Фото', upload_to='posts_images', blank=True)
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        auto_now_add=False,
        help_text='Если установить дату и '
                  'время в будущем — можно делать '
                  'отложенные публикации.'
    )

    author = models.ForeignKey(
        User,
        verbose_name='Автор публикации',
        on_delete=models.CASCADE,
        blank=False
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Категория',
        null=True,
        blank=False
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Местоположение',
        null=True
    )

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'

    def __str__(self):
        return self.title


class Comment(models.Model):
    text = models.TextField("Текст")
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Пост",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    class Meta:
        ordering = ('created_at',)
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self):
        return self.text[:settings.MAX_SELF_COMMENT_LENGTH]
