from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        verbose_name='Название группы',
        max_length=200,
    )
    slug = models.SlugField(
        verbose_name='Адрес группы',
        unique=True,
    )
    description = models.TextField(
        verbose_name='Описание группы',
    )

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Графоманить здесь',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор поста',
        on_delete=models.CASCADE,
        related_name='posts',
    )
    group = models.ForeignKey(
        Group,
        verbose_name='Группа поста',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        help_text='Выбери группу, если хочешь',
    )
    # Поле для картинки (необязательное)
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='posts/',
        blank=True,
        help_text='Добавь картинку, если хочешь',
    )
    # Аргумент upload_to указывает директорию
    # в которую будут загружаться пользовательские файлы.

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        verbose_name='Коммент поста',
        on_delete=models.CASCADE,
        related_name='comments',

    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор коммента',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField(
        verbose_name='Текст коммента',
        help_text='Напиши коммент',
    )
    created = models.DateTimeField(
        verbose_name='Дата коммента',
        auto_now_add=True,
    )

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Подщписщик',
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='following',
    )
