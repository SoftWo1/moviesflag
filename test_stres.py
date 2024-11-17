import unittest
from unittest.mock import patch, Mock
import time
import threading
from app import app

class StressTestMovieWithFlagAppTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up a Flask test client for the entire test class
        cls.client = app.test_client()
        app.config['TESTING'] = True

    def stress_test_movie_searchapi(self):
        def make_request():
            response = self.client.get("/api/movies?filter=superman")
            self.assertEqual(response.status_code, 200)

        num_threads = 50
        threads = []

        for _ in range(num_threads):
            thread = threading.Thread(target=make_request)
            thread.start()
            threads.append(thread)

        # Esperar a que todos los hilos terminen
        for thread in threads:
            thread.join()



    @patch("app.searchfilms")
    @patch("app.getmoviedetails")
    def test_movie_flag_get(self, mock_getmoviedetails, mock_searchfilms):
        mock_getmoviedetails.return_value = {
            "Title": "Superman II",
            "Year": "1980",
            "Country": "United States, United Kingdom, Canada, France",
        }
        mock_searchfilms.return_value = {
            "Search": [
                {
                "Title": "Superman II",
                "Year": "1980",
                "imdbID": "tt0081573"
                }
            ]
        }

        response = self.client.get("/api/movies?filter=superman")
        self.assertEqual(response.status_code, 200)

        # The response should be JSON and contain data
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        for movie in data:
            self.assertEqual(movie["title"], "Superman II")
            self.assertEqual(movie["year"], "1980")
            self.assertEqual(len(movie["countries"]), 4)
            self.assertEqual(movie["countries"][0]["name"], "United States")
            self.assertEqual(movie["countries"][1]["name"], "United Kingdom")
            self.assertEqual(movie["countries"][2]["name"], "Canada")
            self.assertEqual(movie["countries"][3]["name"], "France")
            self.assertEqual(movie["countries"][0]["flag"], "https://flagcdn.com/us.svg")
            self.assertEqual(movie["countries"][1]["flag"], "https://flagcdn.com/gb.svg")
            self.assertEqual(movie["countries"][2]["flag"], "https://flagcdn.com/ca.svg")
            self.assertEqual(movie["countries"][3]["flag"], "https://flagcdn.com/fr.svg")

    @patch("app.get_country_flag")
    @patch("app.getmoviedetails")
    def test_movie_searchapi(self, mock_getmoviedetails, mock_get_country_flag):
        mock_getmoviedetails.return_value = {
            "Title": "Superman II",
            "Year": "1980",
            "Country": "United States, United Kingdom, Canada, France",
        }
        mock_get_country_flag.return_value = "https://flagcdn.com/us.svg"

        response = self.client.get("/api/movies?filter=superman")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 10)
        for movie in data:
            self.assertEqual(movie["title"], "Superman II")
            self.assertEqual(movie["year"], "1980")
            self.assertEqual(len(movie["countries"]), 4)
            self.assertEqual(movie["countries"][0]["name"], "United States")
            self.assertEqual(movie["countries"][1]["name"], "United Kingdom")
            self.assertEqual(movie["countries"][2]["name"], "Canada")
            self.assertEqual(movie["countries"][3]["name"], "France")
            self.assertEqual(movie["countries"][0]["flag"], "https://flagcdn.com/us.svg")
            self.assertEqual(movie["countries"][1]["flag"], "https://flagcdn.com/us.svg")
            self.assertEqual(movie["countries"][2]["flag"], "https://flagcdn.com/us.svg")
            self.assertEqual(movie["countries"][3]["flag"], "https://flagcdn.com/us.svg")

if __name__ == "__main__":
    unittest.main()
