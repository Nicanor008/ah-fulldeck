from django.urls import reverse
from rest_framework.test import APITestCase, APIClient


class TestBaseCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.signup_url = reverse('app_authentication:signup')
        self.login_url = reverse('app_authentication:login')
        self.create_list_article_url = reverse('articles:articles')
        self.get_tags_url = reverse('articles:articles-tags')
        self.list_users_url = reverse('profiles:profile_list')
        self.test_user = {
            'user': {
                'username': 'testuser',
                'email': 'test@user.com',
                'password': 'TestUser123'
            }}
        self.test_user2 = {
            'user': {
                'username': 'testuser2',
                'email': 'test2@user.com',
                'password': 'TestUser123'
            }}
        self.article = {
            "article": {
                "title": "Test Article",
                "description": "Test description for the article",
                "body": "Test body for the article",
                "tags": ["test", "tags"],
                "author": 1
            }
        }
        self.rating = {
            "rating": {
                "rating": 5
            }
        }
        self.bad_Rating = {
            "rating": {
                "rating": 7
            }
        }
        self.no_email = ['email']
        self.no_username = ['username']
        self.no_password = ['password']

        self.comment = {
            "comment": {
                "body": "This is a test comment body."
            }
        }
        self.highlight_data = {
            "start_index": 1,
            "end_index": 4,
            "body": "This is not epic at all"
        }
        self.start_index_greater_than_end_index = {
            "start_index": 4,
            "end_index": 1,
            "body": "This is not epic at all"
        }
        self.highlight_index_not_integer = {
            "start_index": "1",
            "end_index": 5,
            "body": "This is not epic at all"
        }
        self.highlight_out_of_range = {
            "start_index": 1,
            "end_index": 100,
            "body": "This is not epic at all"
        }
        self.missing_highlight_field = {
            "end_index": 4,
            "body": "This is not epic at all"}
        self.report_message = {
            "report": {
                "report_msg": "This article is offensive"
            }
        }

    def remove_data(self, keys=None):
        if keys:
            for key in keys:
                del self.test_user['user'][key]
        return self.test_user

    def signup_user(self):
        return self.client.post(self.signup_url,
                                self.test_user,
                                format='json')

    def signup_user2(self):
        return self.client.post(self.signup_url,
                                self.test_user2,
                                format='json')

    def login_user(self):
        self.signup_user()
        try:
            self.remove_data(self.no_username)
        except Exception:
            pass
        response = self.client.post(self.login_url,
                                    self.test_user,
                                    format='json')
        token = response.data['token']
        return token

    def login_user2(self):
        self.signup_user2()
        response = self.client.post(self.login_url,
                                    self.test_user2,
                                    format='json')
        token = response.data['token']
        return token

    def authorize(self):
        token = self.login_user2()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

    def create_article(self):
        token = self.login_user()
        url = self.create_list_article_url
        response = self.client.post(
            url, self.article, format='json',
            HTTP_AUTHORIZATION="Token " + token)
        slug = response.data['slug']
        return slug

    def single_article_url(self, slug):
        url = reverse('articles:article-details', args=[slug])
        return url

    def single_article_details(self):
        slug = self.create_article()
        url = reverse('articles:article-details',  args=[slug])
        return url

    def create_comment(self, slug):
        url = reverse("articles:comments", kwargs={"slug": slug})
        return url

    def add_comment(self, slug):
        url = self.create_comment(slug)
        token = self.login_user()
        response = self.client.post(
            url,
            self.comment,
            format="json",
            HTTP_AUTHORIZATION="Token " + token
        )
        return response

    def get_comment(self, id):
        url = reverse('articles:comment-details',
                      kwargs={"id": id})
        return url

    def specific_comment(self, slug, id):
        url = reverse('articles:comment-details',
                      kwargs={"slug": slug, "id": id})
        return url

    def update_comment(self):
        token = self.login_user()
        slug = self.create_article()
        response = self.add_comment(slug)
        id = response.data['id']
        response = self.client.put(
            (self.specific_comment(slug, id)),
            data={'comment': {'body': 'New comment'}},
            format='json',
            HTTP_AUTHORIZATION="Token " + token)
        return response

    def like_arcticle_url(self, slug):
        url = reverse('articles:article_like', args=[slug])
        return url

    def dislike_article_url(self, slug):
        return reverse('articles:article_dislike', args=[slug])

    def rating_url(self, slug):
        url = reverse('articles:rate-articles', args=[slug])
        return url

    def ratings_url(self, slug):
        url = reverse('articles:article-ratings', args=[slug])
        return url

    def like_comment_url(self, id):
        url = reverse('articles:comments_like', kwargs={'id': id})
        return url

    def favorite_article_url(self, slug):
        url = reverse('articles:article-favorite', args=[slug])
        return url

    def my_favorites_url(self):
        url = reverse('articles:all_favourites')
        return url

    def rate_article(self, slug):
        url = self.rating_url(slug)
        token = self.login_user2()
        response = self.client.post(
            url,
            self.rating,
            format="json",
            HTTP_AUTHORIZATION="Token " + token
        )
        return response

    def bookmark_article_url(self, slug):
        url = reverse('articles:article-bookmark', kwargs={"slug": slug})
        return url

    def get_bookmarks_url(self):
        url = reverse('articles:article-bookmarks')
        return url

    def edit_history_url(self, slug, id):
        url = reverse('articles:comment-history',
                      kwargs={"slug": slug, "id": id})
        return url

    def highlight_url(self, slug):
        url = reverse('articles:highlighttext', kwargs={"slug": slug})
        return url

    def article_email_share_url(self, slug):
        url = reverse('articles:email_share_article', kwargs={"slug": slug})
        return url

    def article_twitter_share_url(self, slug):
        url = reverse('articles:twitter-share-article', kwargs={"slug": slug})
        return url

    def article_facebook_share_url(self, slug):
        url = reverse('articles:facebook-share-article', kwargs={"slug": slug})
        return url

    def view_single_article(self):
        response = self.client.get(self.single_article_details())
        return response

    def article_stats(self):
        token = self.login_user()
        response = self.client.get(reverse(
            'articles:article-stats'),
            HTTP_AUTHORIZATION="Token " + token, format="json")
        return response
