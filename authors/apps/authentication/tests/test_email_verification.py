# Django imports
from rest_framework.views import status

# local imports
from .base_test import TestBaseCase


class TestEmailVerification(TestBaseCase):

    def test_verify_email(self):
        response = self.signup_user()
        token = response.data['user_info']['token']
        # hit the api endpoint
        verify_url = "/api/v1/verify/{}".format(token)
        res = self.client.get(verify_url)
        message = 'Email has been verified successfully, thank you!'
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(message.encode(), res.content)
