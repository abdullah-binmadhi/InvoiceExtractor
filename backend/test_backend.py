import os
import sys
import unittest
from app import create_app
from database import init_db, get_db
import tempfile
import io

class BackendTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Create a temporary database for testing
        with self.app.app_context():
            init_db()

    def tearDown(self):
        """Clean up after tests"""
        # Clean up database
        pass

    def test_index(self):
        """Test the index route"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('message', data)

    def test_upload_no_file(self):
        """Test upload endpoint with no file"""
        response = self.client.post('/api/upload')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

    def test_login_success(self):
        """Test successful login"""
        response = self.client.post('/api/login', 
                                  json={'username': 'admin', 'password': 'password'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('message', data)
        self.assertIn('user_id', data)

    def test_login_failure(self):
        """Test failed login"""
        response = self.client.post('/api/login', 
                                  json={'username': 'admin', 'password': 'wrong'})
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertIn('error', data)

    def test_history_empty(self):
        """Test history endpoint with no documents"""
        response = self.client.get('/api/history')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)

if __name__ == '__main__':
    unittest.main()