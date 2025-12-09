from locust import HttpUser, task, between
import random

class SearchUser(HttpUser):
    wait_time = between(1, 2)
    host = "http://streamlit.local"

    queries = [
        "Show electricity bill payment more than 500",
        "What products did I purchase",
        "Show purchases and services after march",
        "Show saved payments above Rs. 500",
        "show saved payments"
        
    ]

    @task
    def search(self):
        query = random.choice(self.queries)
        self.client.get(f"/api/search?q={query}")
