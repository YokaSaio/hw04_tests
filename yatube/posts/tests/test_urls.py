from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, User, Group


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.not_author = User.objects.create_user(username='test_client')
        cls.group = Group.objects.create(
            title='test_title',
            slug='test_slug'
        )
        cls.post = Post.objects.create(
            text='test text',
            author=cls.author,
            group=cls.group
        )
        cls.template_url_names = {
            reverse('posts:index'): ['posts/index.html', HTTPStatus.OK],
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}):
                ['posts/group_list.html', HTTPStatus.OK],
            reverse('posts:profile', kwargs={'username': cls.author.username}):
                ['posts/profile.html', HTTPStatus.OK],
            reverse('posts:post_detail', kwargs={'post_id': cls.post.pk}):
                ['posts/post_detail.html', HTTPStatus.OK],
            reverse('posts:post_create'):
                ['posts/create_post.html', HTTPStatus.FOUND],
            reverse('posts:post_edit', kwargs={'post_id': cls.post.pk}):
                ['posts/create_post.html', HTTPStatus.FOUND],
        }
        cls.url_names_https_status_auth = {
            '/': HTTPStatus.OK,
            f'/group/{cls.group.slug}/': HTTPStatus.OK,
            f'/profile/{cls.author.username}/': HTTPStatus.OK,
            '/unexciting_page/': HTTPStatus.NOT_FOUND
        }

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.not_author)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)

    def test_urls_guest(self):
        """Страницы недоступны неавторизованному юзеру"""
        for address, template in self.template_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, template[1])

    def test_post_create_url_available_authorized_user(self):
        """Страница создания поста доступна авторизованному клиенту."""
        response = self.authorized_client.get('/create/', follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_uses_correct_templates(self):
        """url-адрес использует соответсвующий шаблон"""
        for address, template in self.template_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_author.get(
                    address)
                self.assertTemplateUsed(response, template[0])

    def test_redirect_anonymous(self):
        """Перенаправление незарегистрированного
        пользователя на страницу авторизации из url redirect"""
        self.assertRedirects(
            self.guest_client.get(f'/posts/{self.post.id}/edit/'),
            '/auth/login/' + '?next=' + f'/posts/{self.post.id}/edit/')
        self.assertRedirects(
            self.guest_client.get('/create/'),
            '/auth/login/' + '?next=' + '/create/')
