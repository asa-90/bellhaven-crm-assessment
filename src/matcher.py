import json
from pathlib import Path

from rapidfuzz.fuzz import ratio

from normalizer import (
    normalize_address,
    normalize_city,
    normalize_name,
    normalize_phone,
    normalize_state,
    normalize_zip,
)


BASE_DIR = Path(__file__).resolve().parent.parent

WEBSITE_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "bellhaven_locations.json"
)

CRM_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "crm_accounts.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "match_candidates.json"
)


def load_json(file_path):
    """Load JSON data from a file."""

    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def calculate_match_evidence(
    website,
    crm,
):
    """
    Compare one website location
    against one CRM account.
    """

    website_name = normalize_name(
        website.get("name")
    )

    crm_name = normalize_name(
        crm.get("name")
    )

    website_address = normalize_address(
        website.get("address")
    )

    crm_address = normalize_address(
        crm.get("billing_street")
    )

    website_city = normalize_city(
        website.get("city")
    )

    crm_city = normalize_city(
        crm.get("billing_city")
    )

    website_state = normalize_state(
        website.get("state")
    )

    crm_state = normalize_state(
        crm.get("billing_state")
    )

    website_zip = normalize_zip(
        website.get("zip_code")
    )

    crm_zip = normalize_zip(
        crm.get("billing_zip")
    )

    website_phone = normalize_phone(
        website.get("phone")
    )

    crm_phone = normalize_phone(
        crm.get("phone")
    )

    evidence = {
        "name_similarity": round(
            ratio(
                website_name,
                crm_name,
            ),
            1,
        ),
        "address_match": (
            bool(website_address)
            and website_address == crm_address
        ),
        "city_match": (
            bool(website_city)
            and website_city == crm_city
        ),
        "state_match": (
            bool(website_state)
            and website_state == crm_state
        ),
        "zip_match": (
            bool(website_zip)
            and website_zip == crm_zip
        ),
        "phone_match": (
            bool(website_phone)
            and website_phone == crm_phone
        ),
        "website_zip": website_zip,
        "crm_zip": crm_zip,
    }

    return evidence


def calculate_score(evidence):
    """
    Calculate a matching score based
    on multiple independent signals.
    """

    score = 0

    # Phone is a strong identifier.
    if evidence["phone_match"]:
        score += 50

    # Exact street address is also strong.
    if evidence["address_match"]:
        score += 40

    # ZIP provides useful geographic evidence.
    if evidence["zip_match"]:
        score += 20

    # City provides supporting evidence.
    if evidence["city_match"]:
        score += 10

    # State is weak evidence because
    # many Bellhaven locations can share a state.
    if evidence["state_match"]:
        score += 5

    # Name similarity is supporting evidence.
    if evidence["name_similarity"] >= 90:
        score += 20

    elif evidence["name_similarity"] >= 75:
        score += 10

    elif evidence["name_similarity"] >= 60:
        score += 5

    return score


def find_candidates(
    website,
    crm_accounts,
    limit=5,
):
    """
    Find the strongest CRM candidates
    for one website location.
    """

    candidates = []

    for crm in crm_accounts:

        evidence = calculate_match_evidence(
            website,
            crm,
        )

        score = calculate_score(
            evidence
        )

        candidates.append(
            {
                "crm_account_id": crm[
                    "account_id"
                ],
                "crm_name": crm["name"],
                "crm_parent_id": crm.get(
                    "parent_id",
                    "",
                ),
                "crm_parent": crm.get(
                    "parent_name",
                    "",
                ),
                "crm_status": crm.get(
                    "status",
                    "",
                ),
                "crm_address": crm.get(
                    "billing_street",
                    "",
                ),
                "crm_city": crm.get(
                    "billing_city",
                    "",
                ),
                "crm_state": crm.get(
                    "billing_state",
                    "",
                ),
                "crm_zip": crm.get(
                    "billing_zip",
                    "",
                ),
                "crm_phone": crm.get(
                    "phone",
                    "",
                ),
                "lifetime_revenue": crm.get(
                    "lifetime_revenue",
                    0,
                ),
                "outstanding_ar": crm.get(
                    "outstanding_ar",
                    0,
                ),
                "chow_current_account": crm.get(
                    "chow_current_account",
                    "",
                ),
                "duplicate_of_account": crm.get(
                    "duplicate_of_account",
                    "",
                ),
                "score": score,
                "evidence": evidence,
            }
        )

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return candidates[:limit]


def build_match_results(
    website_locations,
    crm_accounts,
):
    """
    Generate candidate matches for
    every website location.
    """

    results = []

    for location in website_locations:

        candidates = find_candidates(
            location,
            crm_accounts,
        )

        results.append(
            {
                "website": location,
                "candidates": candidates,
            }
        )

    return results


def save_json(
    data,
    file_path,
):
    """Save data as formatted JSON."""

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        file_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


if __name__ == "__main__":

    print(
        "Loading website locations..."
    )

    website_locations = load_json(
        WEBSITE_FILE
    )

    print(
        "Loading CRM accounts..."
    )

    crm_accounts = load_json(
        CRM_FILE
    )

    print(
        f"Website locations: "
        f"{len(website_locations)}"
    )

    print(
        f"CRM accounts: "
        f"{len(crm_accounts)}"
    )

    print(
        "\nRunning matching engine..."
    )

    results = build_match_results(
        website_locations,
        crm_accounts,
    )

    save_json(
        results,
        OUTPUT_FILE,
    )

    print(
        f"\nSaved matching results to:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nTop candidate for each location:"
    )

    print(
        "=" * 70
    )

    for result in results:

        website = result["website"]

        candidates = result["candidates"]

        top = candidates[0]

        print(
            f"\n{website['name']}"
        )

        print(
            f"  -> {top['crm_name']}"
        )

        print(
            f"  Score: {top['score']}"
        )

        print(
            f"  Parent: {top['crm_parent']}"
        )

        print(
            "  Evidence:"
        )

        print(
            f"    Name similarity: "
            f"{top['evidence']['name_similarity']}"
        )

        print(
            f"    Address match: "
            f"{top['evidence']['address_match']}"
        )

        print(
            f"    City match: "
            f"{top['evidence']['city_match']}"
        )

        print(
            f"    State match: "
            f"{top['evidence']['state_match']}"
        )

        print(
            f"    ZIP match: "
            f"{top['evidence']['zip_match']}"
        )

        print(
            f"    Phone match: "
            f"{top['evidence']['phone_match']}"
        )