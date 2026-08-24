import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

REVIEW_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "review_queue.json"
)


def load_json(file_path):
    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def money(value):
    if value is None:
        return "$0"

    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return str(value)


def audit_needs_fix(items):

    print("\n")
    print("=" * 80)
    print("NEEDS_FIX")
    print("=" * 80)

    needs_fix = [
        item
        for item in items
        if item["classification"]
        == "NEEDS_FIX"
    ]

    print(
        f"Count: {len(needs_fix)}"
    )

    for index, item in enumerate(
        needs_fix,
        start=1,
    ):

        website = item["website"]
        crm = item["crm"]
        evidence = item["evidence"]

        print("\n" + "-" * 80)

        print(
            f"{index}. "
            f"{website.get('name', '')}"
        )

        print(
            f"   CRM: "
            f"{crm.get('name', '')}"
        )

        print(
            f"   CRM ID: "
            f"{crm.get('account_id', '')}"
        )

        print(
            f"   Parent: "
            f"{crm.get('parent', '')}"
        )

        print(
            f"   Website address: "
            f"{website.get('address', '')}, "
            f"{website.get('city', '')}, "
            f"{website.get('state', '')} "
            f"{website.get('zip_code', '')}"
        )

        print(
            f"   CRM address: "
            f"{crm.get('address', '')}, "
            f"{crm.get('city', '')}, "
            f"{crm.get('state', '')} "
            f"{crm.get('zip', '')}"
        )

        print(
            f"   Score: "
            f"{evidence.get('score')}"
        )

        print(
            f"   Name similarity: "
            f"{evidence.get('name_similarity')}"
        )

        print(
            f"   Address match: "
            f"{evidence.get('address_match')}"
        )

        print(
            f"   City match: "
            f"{evidence.get('city_match')}"
        )

        print(
            f"   State match: "
            f"{evidence.get('state_match')}"
        )

        print(
            f"   ZIP match: "
            f"{evidence.get('zip_match')}"
        )

        print(
            f"   Phone match: "
            f"{evidence.get('phone_match')}"
        )

        print(
            f"   Lifetime revenue: "
            f"{money(crm.get('lifetime_revenue'))}"
        )

        print(
            f"   Outstanding AR: "
            f"{money(crm.get('outstanding_ar'))}"
        )

        print(
            f"   CHOW current account: "
            f"{crm.get('chow_current_account')}"
        )

        print(
            f"   Duplicate of: "
            f"{crm.get('duplicate_of_account')}"
        )

        print(
            f"   Reason: "
            f"{item.get('reason')}"
        )


def audit_no_crm_account(items):

    print("\n")
    print("=" * 80)
    print("NO_CRM_ACCOUNT")
    print("=" * 80)

    no_account = [
        item
        for item in items
        if item["classification"]
        == "NO_CRM_ACCOUNT"
    ]

    print(
        f"Count: {len(no_account)}"
    )

    for index, item in enumerate(
        no_account,
        start=1,
    ):

        website = item["website"]
        candidate = item.get(
            "crm"
        )

        print("\n" + "-" * 80)

        print(
            f"{index}. "
            f"{website.get('name', '')}"
        )

        print(
            f"   Website address: "
            f"{website.get('address', '')}, "
            f"{website.get('city', '')}, "
            f"{website.get('state', '')} "
            f"{website.get('zip_code', '')}"
        )

        print(
            f"   Reason: "
            f"{item.get('reason')}"
        )

        if candidate:
            print(
                f"   Best CRM candidate: "
                f"{candidate.get('name', '')}"
            )

            print(
                f"   Candidate ID: "
                f"{candidate.get('account_id', '')}"
            )

            print(
                f"   Candidate score: "
                f"{item['evidence'].get('score')}"
            )


def audit_crm_only(data):

    print("\n")
    print("=" * 80)
    print("CRM_NOT_ON_WEBSITE")
    print("=" * 80)

    accounts = data.get(
        "crm_not_on_website",
        [],
    )

    print(
        f"Count: {len(accounts)}"
    )

    for index, account in enumerate(
        accounts,
        start=1,
    ):

        print("\n" + "-" * 80)

        print(
            f"{index}. "
            f"{account.get('name', '')}"
        )

        print(
            f"   Account ID: "
            f"{account.get('account_id', '')}"
        )

        print(
            f"   Parent: "
            f"{account.get('parent_name', '')}"
        )

        print(
            f"   Address: "
            f"{account.get('billing_street', '')}, "
            f"{account.get('billing_city', '')}, "
            f"{account.get('billing_state', '')} "
            f"{account.get('billing_zip', '')}"
        )

        print(
            f"   Status: "
            f"{account.get('status', '')}"
        )

        print(
            f"   Lifetime revenue: "
            f"{money(account.get('lifetime_revenue'))}"
        )

        print(
            f"   Outstanding AR: "
            f"{money(account.get('outstanding_ar'))}"
        )

        print(
            f"   CHOW current account: "
            f"{account.get('chow_current_account')}"
        )

        print(
            f"   Duplicate of: "
            f"{account.get('duplicate_of_account')}"
        )


if __name__ == "__main__":

    print(
        "Loading review queue..."
    )

    data = load_json(
        REVIEW_FILE
    )

    items = data["items"]

    print(
        f"Total items: {len(items)}"
    )

    audit_needs_fix(items)

    audit_no_crm_account(items)

    audit_crm_only(data)

    print("\n")
    print("=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)