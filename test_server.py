import unittest
import json
import os
from server import app
import uuid

class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        """Set up test client before each test"""
        self.app = app.test_client()
        self.app.testing = True

    def test_index(self):
        """Test if the index page loads correctly"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'user_id', response.data)
        print("test_index: Aman - Index page loads correctly")

    def test_upload_excel(self):
        """Test uploading an Excel file"""
        file_path = 'user_excel/test.xlsx'  # Pastikan file ini ada di direktori project
        user_id = str(uuid.uuid4())  # Generate UUID

        # Set user_id ke session sebelum melakukan POST
        with self.app.session_transaction() as sess:
            sess['user_id'] = user_id

        with open(file_path, 'rb') as file:
            data = {
                'file': (file, 'test.xlsx'),
                'user_id': user_id  # Sertakan User ID di form data jika perlu
            }
            response = self.app.post('/upload-excel', data=data, content_type='multipart/form-data')

        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data)
        
        # Periksa apakah respons mengandung 'message' atau 'error'
        if 'message' in response_json:
            self.assertEqual(response_json['message'], "File uploaded and processed successfully")
            print("test_upload_excel: Aman - File uploaded successfully")
        elif 'error' in response_json:
            self.assertEqual(response_json['error'], "User ID is not set. Please generate UUID first.")
            print("test_upload_excel: Error - User ID not set")
        else:
            self.fail("Unexpected response from server")
            print("test_upload_excel: Fail - Unexpected response")

    def test_process_user_input(self):
        """Test processing user input"""
        data = {
            'containertype': 20,
            'masked_name': 'ID_7',
            'comm_grade_ro': 'MINUMAN (A)',
            'qty_ro': 5,
            'user_id': '1cfbd576-54a0-4c41-9031-c1222d952f11'
        }
        response = self.app.post('/process-user_input', data=data)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data)
        self.assertIn('prediction', response_json)
        print("test_process_user_input: Aman - User input processed correctly")

    def test_process_multiple_user_inputs(self):
        """Test processing multiple user inputs"""
        
        # Data input untuk beberapa instance sekaligus
        data = [
            {
                'containertype': 40,
                'masked_name': 'ID_0',
                'comm_grade_ro': 'GENERAL CARGO (B)',
                'qty_ro': 7,
                'user_id': '1cfbd576-54a0-4c41-9031-c1222d952f11'
            },
            {
                'containertype': 20,
                'masked_name': 'ID_0',
                'comm_grade_ro': 'MINUMAN (A)',
                'qty_ro': 5,
                'user_id': '1cfbd576-54a0-4c41-9031-c1222d952f11'
            },
            {
                'containertype': 20,
                'masked_name': 'ID_8',
                'comm_grade_ro': 'KARTON (A)',
                'qty_ro': 4,
                'user_id': '1cfbd576-54a0-4c41-9031-c1222d952f11'
            }
        ]

        # Mengirimkan data untuk setiap instance
        predictions = []
        for instance_data in data:
            response = self.app.post('/process-user_input', data=instance_data)
            self.assertEqual(response.status_code, 200)
            response_json = json.loads(response.data)
            self.assertIn('prediction', response_json)
            
            # Menyimpan hasil prediksi untuk setiap instance
            predictions.append(response_json['prediction'])
        
        # Pastikan ada beberapa prediksi
        self.assertGreater(len(predictions), 1)
        print("test_process_multiple_user_inputs: Aman - Multiple user inputs processed correctly")

if __name__ == '__main__':
    unittest.main()
