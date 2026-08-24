import os
from urllib import response

import requests
from dotenv import load_dotenv


load_dotenv()


class CRMClient:
    def __init__(self):
        self.base_url = os.getenv("CRM_BASE_URL")
        self.token = os.getenv("CRM_API_TOKEN")

        if not self.base_url:
            raise ValueError("CRM_BASE_URL is not set")

        if not self.token:
            raise ValueError("CRM_API_TOKEN is not set")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }

    def get_me(self):
        response = requests.get(
            f"{self.base_url}/me",
            headers=self.headers,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def get_accounts(self):
        response = requests.get(
        f"{self.base_url}/accounts",
        headers=self.headers,
        timeout=30,
    )

        response.raise_for_status()

        payload = response.json()

        return payload["data"]


if __name__ == "__main__":
    client = CRMClient()

    me = client.get_me()
    print("ME:")
    print(me)

    accounts = client.get_accounts()

    print("\nACCOUNTS TYPE:")
    print(type(accounts))

    print("\nACCOUNTS:")
    print(accounts)