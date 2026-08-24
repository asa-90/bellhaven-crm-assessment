import json


INPUT_FILE = "data/raw/crm_accounts.json"


with open(
    INPUT_FILE,
    "r",
    encoding="utf-8",
) as file:
    accounts = json.load(file)


print("CRM PROFILE")
print("=" * 50)

print(f"Total accounts: {len(accounts)}")


# Status distribution
status_counts = {}

for account in accounts:
    status = account.get("status", "")

    status_counts[status] = (
        status_counts.get(status, 0) + 1
    )


print("\nSTATUS")
print("-" * 50)

for status, count in status_counts.items():
    print(f"{status}: {count}")


# Parent distribution
parent_counts = {}

for account in accounts:
    parent = account.get(
        "parent_name",
        "",
    )

    if not parent:
        parent = "[NO PARENT]"

    parent_counts[parent] = (
        parent_counts.get(parent, 0) + 1
    )


print("\nPARENT COMPANIES")
print("-" * 50)

for parent, count in sorted(
    parent_counts.items(),
    key=lambda item: item[1],
    reverse=True,
):
    print(f"{parent}: {count}")


# Revenue
revenue_accounts = [
    account
    for account in accounts
    if account.get("lifetime_revenue", 0) > 0
]


print("\nREVENUE")
print("-" * 50)

print(
    f"Accounts with lifetime revenue: "
    f"{len(revenue_accounts)}"
)


# Outstanding AR
ar_accounts = [
    account
    for account in accounts
    if account.get("outstanding_ar", 0) > 0
]


print(
    f"Accounts with outstanding AR: "
    f"{len(ar_accounts)}"
)


# Duplicate flags
duplicate_accounts = [
    account
    for account in accounts
    if account.get("duplicate_of_account")
]


print(
    f"Accounts marked as duplicate: "
    f"{len(duplicate_accounts)}"
)