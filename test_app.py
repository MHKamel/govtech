import json
import unittest
from unittest.mock import patch
from app import app

class TestFlaskApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_index_route(self):
        # Test that the index route returns status code 200
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    @patch('app.request')
    def test_update_graph_route(self, mock_request):
        # Test that the update_graph route returns status code 200 with mock request data
        mock_request.form.get.return_value = 'selected_value'
        response = self.app.post('/update_graph')
        self.assertEqual(response.status_code, 200)

        # Test that the response contains expected data
        data = json.loads(response.data)
        self.assertIn('graphJSON', data)

if __name__ == '__main__':
    unittest.main()
