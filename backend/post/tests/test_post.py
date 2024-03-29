from random import randint
from uuid import UUID, uuid1
from factory.fuzzy import FuzzyText

from django.urls import reverse
from rest_framework import status

from blog import settings
from blog.factories import CategoryFactory, PostFactory, UserFactory
from blog.utils import BasicAPITestCase
from post.models import Post


class PostCreateTestCase(BasicAPITestCase):
    def setUp(self) -> None:
        self.data = {
            'title': FuzzyText().fuzz(),
            'body': FuzzyText().fuzz(),
            'category': CategoryFactory().title,
        }

    def _request(self, data: dict, is_auth: bool = True):
        if is_auth:
            self._auth(UserFactory())
        return self.client.post(
            reverse('api_post_create_list'),
            data=data,
        )

    def test_success_create_post(self):
        response = self._request(self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(Post.objects.all()), 1)

    def test_failure_create_post_with_long_title(self):
        data = {
            'title': FuzzyText(length=129).fuzz(),
        }
        response = self._request(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(len(Post.objects.all()))

    def test_failure_create_post_without_body(self):
        data = {
            'title': FuzzyText().fuzz(),
        }
        response = self._request(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(len(Post.objects.all()))

    def test_failure_create_post_without_title(self):
        data = {
            'body': FuzzyText().fuzz(),
        }
        response = self._request(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(len(Post.objects.all()))

    def test_failure_create_post_without_auth(self):
        response = self._request(self.data, is_auth=False)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(len(Post.objects.all()))


class PostGetListTestCase(BasicAPITestCase):

    def _request(self, is_auth: bool = True):
        if is_auth:
            self._auth(UserFactory())
        return self.client.get(
            reverse('api_post_create_list'),
        )

    def test_success_get_list_posts(self):
        count_posts = randint(5, settings.REST_FRAMEWORK['PAGE_SIZE'])
        for _ in range(count_posts):
            PostFactory()

        response = self._request()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), count_posts)
        self.assertEqual(len(Post.objects.all()), count_posts)

    def test_success_get_list_posts_in_draft_without_auth(self):
        count_posts_not_as_draft = \
            randint(5, settings.REST_FRAMEWORK['PAGE_SIZE'])
        for _ in range(count_posts_not_as_draft):
            PostFactory()
        count_posts_as_draft = randint(5, settings.REST_FRAMEWORK['PAGE_SIZE'])
        for _ in range(count_posts_as_draft):
            PostFactory(is_draft=True)

        response = self._request(is_auth=False)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.json()['results']),
            count_posts_not_as_draft,
        )
        self.assertEqual(
            len(Post.objects.all()),
            count_posts_not_as_draft + count_posts_as_draft,
        )


class PostGetTestCase(BasicAPITestCase):
    def setUp(self) -> None:
        self.data = {
            'title': FuzzyText().fuzz(),
            'body': FuzzyText().fuzz(),
            'category': CategoryFactory(),
        }

    def _request(self, id: UUID):
        return self.client.get(
            reverse('api_post_get_put_patch_delete', args=[id]),
        )

    def test_success_get_post(self):
        post = PostFactory(**self.data)

        response = self._request(post.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(Post.objects.all()), 1)
        self.assertEqual(len(Post.objects.filter(pk=post.pk)), 1)
        post: Post = Post.objects.filter(pk=post.pk)[0]
        self.assertEqual(post.body, self.data['body'])
        self.assertEqual(post.title, self.data['title'])

    def test_failure_get_post_if_not_exist(self):
        response = self._request(uuid1())
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class PostUpdateTestCase(BasicAPITestCase):
    def setUp(self) -> None:
        self.data = {
            'title': FuzzyText().fuzz(),
            'body': FuzzyText().fuzz(),
            'category': CategoryFactory().title,
        }

    def _request(self, id: UUID, data: dict, is_auth: bool = True):
        if is_auth:
            self._auth(UserFactory())
        return self.client.put(
            reverse('api_post_get_put_patch_delete', args=[id]),
            data=data,
        )

    def test_success_update_post(self):
        post = PostFactory()
        response = self._request(post.pk, self.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post: Post = Post.objects.filter(pk=post.pk)[0]
        self.assertEqual(post.body, self.data['body'])
        self.assertEqual(post.title, self.data['title'])

    def test_failure_update_post_if_not_exist(self):
        response = self._request(1, self.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_failure_update_post_without_auth(self):
        post = PostFactory()
        response = self._request(post.pk, self.data, is_auth=False)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        new_post: Post = Post.objects.filter(pk=post.pk)[0]
        self.assertEqual(new_post.body, post.body)
        self.assertEqual(new_post.title, post.title)


class PostDeleteTestCase(BasicAPITestCase):

    def _request(self, id: UUID, is_auth: bool = True):
        if is_auth:
            self._auth(UserFactory())
        return self.client.delete(
            reverse('api_post_get_put_patch_delete', args=[id]),
        )

    def test_success_delete_post(self):

        post = PostFactory()
        response = self._request(post.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(len(Post.objects.all()))

    def test_failure_delete_post_without_auth(self):
        post = PostFactory()
        response = self._request(post.pk, is_auth=False)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(Post.objects.all()), 1)
