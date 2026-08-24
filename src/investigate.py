import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

CRM_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "crm_accounts.json"
)


def load_json(path):
    with open(
        path,
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def show_account(account):
    print("-" * 90)

    print(
        f"Name: {account.get('name', '')}"
    )

    print(
        f"ID: {account.get('account_id', '')}"
    )

    print(
        f"Parent ID: {account.get('parent_id', '')}"
    )

    print(
        f"Parent: {account.get('parent_name', '')}"
    )

    print(
        f"Status: {account.get('status', '')}"
    )

    print(
        f"Address: "
        f"{account.get('billing_street', '')}, "
        f"{account.get('billing_city', '')}, "
        f"{account.get('billing_state', '')} "
        f"{account.get('billing_zip', '')}"
    )

    print(
        f"Phone: {account.get('phone', '')}"
    )

    print(
        f"Lifetime revenue: "
        f"{account.get('lifetime_revenue', 0)}"
    )

    print(
        f"Outstanding AR: "
        f"{account.get('outstanding_ar', 0)}"
    )

    print(
        f"CHOW current account: "
        f"{account.get('chow_current_account', '')}"
    )

    print(
        f"Duplicate of: "
        f"{account.get('duplicate_of_account', '')}"
    )

    print(
        f"Note: {account.get('note', '')}"
    )


if __name__ == "__main__":

    accounts = load_json(
        CRM_FILE
    )

    print(
        f"Total CRM accounts: {len(accounts)}"
    )

    print("\nBELLHAVEN / POTENTIAL BELLHAVEN ACCOUNTS")
    print("=" * 90)

    for account in accounts:

        name = (
            account.get("name", "")
            .lower()
        )

        parent = (
            account.get("parent_name", "")
            .lower()
        )

        if (
            "bellhaven" in name
            or "bellhaven" in parent
        ):
            show_account(account)

    print("\nPOSSIBLE OWOSSO DUPLICATES")
    print("=" * 90)

    for account in accounts:

        text = (
            account.get("name", "")
            .lower()
        )

        if "owosso" in text:
            show_account(account)