import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class CRMClient:
    """
    Client for the Bellhaven CRM Sandbox API.

    Read operations:
        - get_me()
        - get_accounts()
        - get_account()

    Write operations:
        - create_account()
        - update_account()

    IMPORTANT:
    Write operations should only be called after
    explicit reviewer approval in the review application.
    """

    def __init__(self):
        self.base_url = os.getenv("CRM_BASE_URL")
        self.token = os.getenv("CRM_API_TOKEN")

        if not self.base_url:
            raise ValueError(
                "CRM_BASE_URL is not set in .env"
            )

        if not self.token:
            raise ValueError(
                "CRM_API_TOKEN is not set in .env"
            )

        self.base_url = self.base_url.rstrip("/")

        self.session = requests.Session()

        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    # ========================================================
    # GET CURRENT USER
    # ========================================================

    def get_me(self):
        """
        Get the currently authenticated candidate.
        """

        response = self.session.get(
            f"{self.base_url}/me",
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    # ========================================================
    # GET ALL ACCOUNTS
    # ========================================================

    def get_accounts(self):
        """
        Get all CRM accounts.
        """

        response = self.session.get(
            f"{self.base_url}/accounts",
            timeout=30,
        )

        response.raise_for_status()

        payload = response.json()

        if "data" not in payload:
            raise ValueError(
                "CRM response does not contain 'data'"
            )

        return payload["data"]

    # ========================================================
    # GET SINGLE ACCOUNT
    # ========================================================

    def get_account(self, account_id):
        """
        Get one CRM account by account ID.
        """

        if not account_id:
            raise ValueError(
                "account_id is required"
            )

        response = self.session.get(
            f"{self.base_url}/accounts/{account_id}",
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    # ========================================================
    # CREATE ACCOUNT
    # ========================================================

    def create_account(self, account_data):
        """
        Create a new CRM account.

        This method should ONLY be called after
        reviewer approval.
        """

        if not isinstance(account_data, dict):
            raise TypeError(
                "account_data must be a dictionary"
            )

        response = self.session.post(
            f"{self.base_url}/accounts",
            json=account_data,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    # ========================================================
    # UPDATE ACCOUNT
    # ========================================================

    def update_account(
        self,
        account_id,
        changes,
    ):
        """
        Update an existing CRM account.

        Example:

            client.update_account(
                account_id,
                {
                    "name": "New Account Name"
                }
            )

        This method should ONLY be called after
        reviewer approval.
        """

        if not account_id:
            raise ValueError(
                "account_id is required"
            )

        if not isinstance(changes, dict):
            raise TypeError(
                "changes must be a dictionary"
            )

        if not changes:
            raise ValueError(
                "changes cannot be empty"
            )

        response = self.session.patch(
            f"{self.base_url}/accounts/{account_id}",
            json=changes,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()


# ============================================================
# TEST / DEVELOPMENT
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("CRM API CONNECTION TEST")
    print("=" * 70)

    client = CRMClient()

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    print("\nME:")
    print("-" * 70)

    me = client.get_me()

    print(
        json.dumps(
            me,
            indent=2,
            ensure_ascii=False,
        )
    )

    # --------------------------------------------------------
    # Accounts
    # --------------------------------------------------------

    print("\nCRM ACCOUNTS:")
    print("-" * 70)

    accounts = client.get_accounts()

    print(
        f"Account count: {len(accounts)}"
    )

    # --------------------------------------------------------
    # First account
    # --------------------------------------------------------

    if accounts:

        first_account = accounts[0]

        account_id = (
            first_account.get("account_id")
            or first_account.get("id")
        )

        print("\nFIRST ACCOUNT:")
        print("-" * 70)

        print(
            json.dumps(
                first_account,
                indent=2,
                ensure_ascii=False,
            )
        )

        # ----------------------------------------------------
        # Account detail
        # ----------------------------------------------------

        if account_id:

            print("\nACCOUNT DETAIL:")
            print("-" * 70)

            account_detail = client.get_account(
                account_id
            )

            print(
                json.dumps(
                    account_detail,
                    indent=2,
                    ensure_ascii=False,
                )
            )

    print("\n" + "=" * 70)
    print("API TEST COMPLETE")
    print("=" * 70)