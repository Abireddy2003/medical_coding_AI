from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

class PredictCPTTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('predict_cpt')

    def test_predict_cpt(self):
        response = self.client.post(self.url, {'description': 'MRI scan for head injury'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('predicted_cpt', response.data)
