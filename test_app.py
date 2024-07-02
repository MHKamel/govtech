import unittest
from app import app

class TestApp(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Export', response.data)
        self.assertIn(b'Import', response.data)

    def test_update_year_graph_route(self):
        response = self.app.post('/update_year_graph', data={'year': '2023', 'na_items[]': ['Export']})
        self.assertEqual(response.status_code, 200)

    def test_update_graph_route(self):
        response = self.app.post('/update_graph', data={'country': 'DE', 'na_items[]': ['Import']})
        self.assertEqual(response.status_code, 200)

    def test_country_route(self):
        response = self.app.get('/country')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'DE', response.data)
        self.assertIn(b'Export', response.data)
        self.assertIn(b'Import', response.data)

    def test_update_pie_charts_route(self):
        response = self.app.post('/update_pie_charts', data={'year': '2023', 'country': 'DE'})
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertIn('pieTracesJSON', json_data)

    def test_update_combined_pie_charts_route(self):
        response = self.app.post('/update_combined_pie_charts', json={'country': 'DE'})
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertIn('combinedPieTracesJSON', json_data)

if __name__ == '__main__':
    unittest.main()
