# posts/tests/test_views.py
import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


def field_check(resp, slf):
    # Словарь ожидаемых типов полей формы:
    form_fields = {
        'text': forms.fields.CharField,
        'group': forms.fields.ChoiceField,
        'image': forms.fields.ImageField
    }
    for value, expected in form_fields.items():
        with slf.subTest(value=value):
            form_field = resp.context.get('form').fields.get(value)
            slf.assertIsInstance(form_field, expected)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    def check_object(self, post_object):
        self.assertEqual(post_object.text, self.post.text)
        self.assertEqual(post_object.author, self.post.author)
        self.assertEqual(post_object.group, self.post.group)
        self.assertEqual(post_object.image, self.post.image)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='test-author')
        cls.user_f = User.objects.create(username='test-follower')

        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            slug='test-slug',
            description='Тестовое описание'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=uploaded,
        )
        cls.group_other = Group.objects.create(
            title='Тестовый другой заголовок',
            slug='test-other-slug',
            description='Тестовое другое описание'
        )   # без постов

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.follower_client = Client()

        self.authorized_client.force_login(self.user)
        self.follower_client.force_login(self.user_f)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}
                    ): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'test-author'}
                    ): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}
                    ): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id':
                    self.post.pk}): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверка контекста страниц

    # Главная страница
    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))

        post_object = response.context['page_obj'][0]

        self.check_object(post_object)

    # Страница группы

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:group_list',
                                         kwargs={'slug': 'test-slug'}))

        post_object = response.context['page_obj'][0]

        self.check_object(post_object)
        self.assertEqual(response.context['group'], self.post.group)

    # Страница профиля

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:profile',
                                         kwargs={'username': 'test-author'}))

        post_object = response.context['page_obj'][0]

        self.check_object(post_object)
        self.assertEqual(response.context['author'], self.post.author)

    # Страница поста

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:post_detail',
                                         kwargs={'post_id': self.post.pk}))

        post_object = response.context['post']

        self.check_object(post_object)

    # Страница создания поста

    def test_create_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        field_check(response, self)

    # Страница редактирования поста

    def test_create_edit_show_correct_context(self):
        """Шаблон create_post(edit) сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_edit',
                                              kwargs={'post_id': self.post.pk})
                                              )
        field_check(response, self)

#   Поста не существует в другой группе
    def test_post_showes_correct(self):
        """Другая группа осталась пуста."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-other-slug'}))

        self.assertFalse(response.context['page_obj'])


# Пажинатор


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-author')

        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )

        post_s = [(Post(author=cls.user, text=f'Тестовый текст {i}',
                        group=cls.group)) for i in range(13)]

        cls.post = Post.objects.bulk_create(post_s)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_secomd_pages(self):
        AMMOUNT_PAGE2 = 3
        index_list = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'test-author'}),
        }
        for reverse_name in index_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                response2 = self.authorized_client.get(reverse_name + '?page=2'
                                                       )
                self.assertEqual(len(response.context['page_obj']),
                                 settings.AMOUNT_OF_POSTS)
                self.assertEqual(len(response2.context['page_obj']),
                                 AMMOUNT_PAGE2)

# Кэш


class CacheIndexPageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test-author')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache(self):
        Post.objects.create(
            text='Кеш-пост',
            author=self.user,
        )
        response = self.authorized_client.get(reverse('posts:index'))
        cache.clear()
        response_2 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response, response_2)

# Подписка


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_a = User.objects.create(username='test-autor')
        cls.user_f = User.objects.create(username='test-follower')

        cls.post = Post.objects.create(
            author=cls.user_a,
            text='Тест подписок',
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.follower_client = Client()

        self.authorized_client.force_login(self.user_a)
        self.follower_client.force_login(self.user_f)

    def test_follow_works_correct(self):
        """Тест подписки на пользователя."""
        count_follow = Follow.objects.count()
        self.follower_client.post(reverse('posts:profile_follow',
                                  kwargs={'username': self.user_a}))

        follow = Follow.objects.last()
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author, self.user_a)
        self.assertEqual(follow.user, self.user_f)

        count_follow = Follow.objects.count()
        self.follower_client.post(reverse('posts:profile_unfollow',
                                          kwargs={'username':
                                                  self.user_a}))
        self.assertEqual(Follow.objects.count(), count_follow - 1)
