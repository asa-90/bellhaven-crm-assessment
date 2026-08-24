import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

MATCH_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "match_candidates.json"
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
    / "classified_matches.json"
)


BELLHAVEN_PARENT_NAME = (
    "Bellhaven Senior Living (Parent Account)"
)


def load_json(file_path):
    """Load JSON data."""

    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def classify_website_match(result):
    """
    Classify the best CRM candidate
    for one website location.
    """

    website = result["website"]

    candidates = result["candidates"]

    if not candidates:
        return {
            "classification": "NO_CRM_ACCOUNT",
            "website": website,
            "best_candidate": None,
            "reason": (
                "No CRM candidates were found."
            ),
        }

    best = candidates[0]

    score = best["score"]

    evidence = best["evidence"]

    name_similarity = (
        evidence["name_similarity"]
    )

    strong_identifier_count = sum(
        [
            evidence["address_match"],
            evidence["city_match"],
            evidence["zip_match"],
            evidence["phone_match"],
        ]
    )

    # Very strong match.
    if (
        score >= 100
        and strong_identifier_count >= 2
    ):
        classification = "CONFIDENT_MATCH"

        reason = (
            "Strong multi-field match."
        )

    # Strong name plus geographic evidence,
    # but not enough for an automatic match.
    elif (
        name_similarity >= 90
        and strong_identifier_count >= 1
    ):
        classification = "NEEDS_FIX"

        reason = (
            "Likely match, but one or more "
            "important fields differ."
        )

    # Moderate evidence.
    elif (
        score >= 60
        and strong_identifier_count >= 1
    ):
        classification = "NEEDS_FIX"

        reason = (
            "Potential match requiring "
            "manual review."
        )

    # Weak evidence.
    else:
        classification = "NO_CRM_ACCOUNT"

        reason = (
            "No sufficiently reliable CRM "
            "match was identified."
        )

    return {
        "classification": classification,
        "website": website,
        "best_candidate": best,
        "alternative_candidates": candidates[
            1:
        ],
        "reason": reason,
    }


def classify_all_matches(
    match_results,
):
    """Classify every website location."""

    classified = []

    for result in match_results:

        classification = classify_website_match(
            result
        )

        classified.append(
            classification
        )

    return classified


def find_bellhaven_crm_accounts(
    crm_accounts,
):
    """
    Return CRM accounts currently assigned
    to Bellhaven Senior Living.
    """

    return [
        account
        for account in crm_accounts
        if account.get("parent_name")
        == BELLHAVEN_PARENT_NAME
    ]


def find_website_matched_crm_ids(
    classified_matches,
):
    """
    Return CRM account IDs that were selected
    as website matches.
    """

    matched_ids = set()

    for item in classified_matches:

        candidate = item.get(
            "best_candidate"
        )

        if candidate:

            matched_ids.add(
                candidate[
                    "crm_account_id"
                ]
            )

    return matched_ids


def find_crm_not_on_website(
    crm_accounts,
    classified_matches,
):
    """
    Identify Bellhaven CRM accounts that do
    not appear among website matches.
    """

    bellhaven_accounts = (
        find_bellhaven_crm_accounts(
            crm_accounts
        )
    )

    matched_ids = (
        find_website_matched_crm_ids(
            classified_matches
        )
    )

    missing_from_website = []

    for account in bellhaven_accounts:

        if (
            account["account_id"]
            not in matched_ids
        ):

            missing_from_website.append(
                account
            )

    return missing_from_website


def save_json(
    data,
    file_path,
):
    """Save formatted JSON."""

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
        "Loading matching results..."
    )

    match_results = load_json(
        MATCH_FILE
    )

    print(
        "Loading CRM accounts..."
    )

    crm_accounts = load_json(
        CRM_FILE
    )

    print(
        f"Website locations: "
        f"{len(match_results)}"
    )

    print(
        f"CRM accounts: "
        f"{len(crm_accounts)}"
    )

    print(
        "\nClassifying matches..."
    )

    classified_matches = (
        classify_all_matches(
            match_results
        )
    )

    crm_not_on_website = (
        find_crm_not_on_website(
            crm_accounts,
            classified_matches,
        )
    )

    output = {
        "summary": {
            "website_locations": len(
                match_results
            ),
            "crm_accounts": len(
                crm_accounts
            ),
            "classified_locations": len(
                classified_matches
            ),
            "crm_not_on_website": len(
                crm_not_on_website
            ),
        },
        "matches": classified_matches,
        "crm_not_on_website": (
            crm_not_on_website
        ),
    }

    save_json(
        output,
        OUTPUT_FILE,
    )

    print(
        f"\nSaved classification results to:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nCLASSIFICATION SUMMARY"
    )

    print(
        "=" * 50
    )

    counts = {}

    for item in classified_matches:

        classification = item[
            "classification"
        ]

        counts[classification] = (
            counts.get(
                classification,
                0,
            )
            + 1
        )

    for classification, count in (
        sorted(counts.items())
    ):

        print(
            f"{classification}: {count}"
        )

    print(
        "\nCRM ACCOUNTS NOT ON WEBSITE"
    )

    print(
        "=" * 50
    )

    print(
        f"Count: "
        f"{len(crm_not_on_website)}"
    )

    for account in crm_not_on_website:

        print(
            f"- "
            f"{account['name']} "
            f"({account['account_id']})"
        )