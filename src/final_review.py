import json
from pathlib import Path
from collections import Counter


# ============================================================================
# PATH CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

REVIEW_QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "review_queue.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "final_review.json"
)


# ============================================================================
# JSON HELPERS
# ============================================================================

def load_json(file_path):
    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_json(data, file_path):

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


# ============================================================================
# SAFE HELPERS
# ============================================================================

def safe_string(value):
    """
    Convert None into an empty string so that
    sorting and comparisons never crash.
    """

    if value is None:
        return ""

    return str(value).strip()


def get_decision_action(item):
    """
    Safely extract human review decision.

    Possible values may include:
        MATCH
        NO_MATCH
        REVIEW
        PENDING
        None
    """

    decision = item.get(
        "decision",
        {},
    )

    if not isinstance(decision, dict):
        return ""

    return safe_string(
        decision.get(
            "action",
            "",
        )
    )


def get_recommendation(item):
    """
    Safely extract secondary review recommendation.
    """

    assessment = item.get(
        "review_assessment",
        {},
    )

    if not isinstance(assessment, dict):
        return ""

    return safe_string(
        assessment.get(
            "recommendation",
            "",
        )
    )


# ============================================================================
# FINAL DECISION LOGIC
# ============================================================================

def determine_final_decision(item):
    """
    Determine the current final decision.

    Priority:

    1. Human reviewer decision, if supplied
    2. NO_CRM_ACCOUNT recommendation
    3. CONFIDENT_MATCH recommendation
    4. MANUAL_REVIEW recommendation
    5. Otherwise PENDING

    IMPORTANT:
    This does NOT invent a human decision.

    If the reviewer has not explicitly provided an action,
    the item remains based on the automated assessment.
    """

    action = get_decision_action(
        item
    )

    recommendation = get_recommendation(
        item
    )

    # ------------------------------------------------------------------------
    # Explicit human decision
    # ------------------------------------------------------------------------

    if action:

        normalized_action = (
            action.upper()
        )

        if normalized_action in {
            "MATCH",
            "CONFIRMED_MATCH",
            "CONFIDENT_MATCH",
        }:
            return "MATCH"

        if normalized_action in {
            "NO_MATCH",
            "NO_CRM_ACCOUNT",
            "REJECT",
        }:
            return "NO_MATCH"

        if normalized_action in {
            "REVIEW",
            "MANUAL_REVIEW",
            "PENDING",
        }:
            return "MANUAL_REVIEW"

        return normalized_action

    # ------------------------------------------------------------------------
    # Automated recommendation
    # ------------------------------------------------------------------------

    if recommendation == "NO_CRM_ACCOUNT":

        return "NO_CRM_ACCOUNT"

    if recommendation == "CONFIDENT_MATCH":

        return "MATCH"

    if recommendation == "LIKELY_MATCH":

        return "MANUAL_REVIEW"

    if recommendation == "MANUAL_REVIEW":

        return "MANUAL_REVIEW"

    return "PENDING"


# ============================================================================
# DUPLICATE DETECTION
# ============================================================================

def detect_duplicate_candidates(items):
    """
    Detect CRM accounts that are being used as the best candidate
    for multiple website locations.

    Returns:

        {
            crm_account_id: [
                website_name_1,
                website_name_2,
                ...
            ]
        }
    """

    usage = {}

    for item in items:

        crm = item.get(
            "crm"
        )

        if not crm:
            continue

        account_id = safe_string(
            crm.get(
                "account_id",
                ""
            )
        )

        website = item.get(
            "website",
            {}
        )

        website_name = safe_string(
            website.get(
                "name",
                ""
            )
        )

        if not account_id:
            continue

        if not website_name:
            continue

        usage.setdefault(
            account_id,
            []
        ).append(
            website_name
        )

    duplicates = {}

    for account_id, websites in usage.items():

        if len(websites) > 1:

            duplicates[
                account_id
            ] = websites

    return duplicates


# ============================================================================
# BUILD FINAL ITEM
# ============================================================================

def build_final_item(
    item,
    duplicate_map,
):
    """
    Build final review record while preserving
    the original review queue information.
    """

    website = item.get(
        "website",
        {}
    )

    crm = item.get(
        "crm"
    )

    recommendation = get_recommendation(
        item
    )

    final_decision = determine_final_decision(
        item
    )

    duplicate_info = None

    if crm:

        account_id = safe_string(
            crm.get(
                "account_id",
                ""
            )
        )

        if account_id in duplicate_map:

            duplicate_info = {
                "is_duplicate_candidate": True,
                "crm_account_id": account_id,
                "used_by": duplicate_map[
                    account_id
                ],
            }

    return {
        "website": website,

        "crm": crm,

        "original_classification": item.get(
            "classification",
            ""
        ),

        "original_reason": item.get(
            "reason",
            ""
        ),

        "original_evidence": item.get(
            "evidence"
        ),

        "review_assessment": item.get(
            "review_assessment",
            {}
        ),

        "decision": item.get(
            "decision",
            {
                "status": "PENDING",
                "action": None,
                "reviewer_note": "",
            }
        ),

        "final_decision": final_decision,

        "duplicate_check": (
            duplicate_info
            if duplicate_info
            else {
                "is_duplicate_candidate": False
            }
        ),
    }


# ============================================================================
# SUMMARY
# ============================================================================

def build_summary(
    items,
    duplicate_map,
):
    """
    Build final review summary.

    Sorting is performed using safe string conversion
    so None values can never cause a TypeError.
    """

    original_classification = Counter()

    final_decision = Counter()

    recommendation = Counter()

    manual_review_items = []

    duplicate_items = []

    for item in items:

        classification = safe_string(
            item.get(
                "original_classification",
                ""
            )
        )

        if not classification:
            classification = "UNKNOWN"

        original_classification[
            classification
        ] += 1

        decision = safe_string(
            item.get(
                "final_decision",
                ""
            )
        )

        if not decision:
            decision = "PENDING"

        final_decision[
            decision
        ] += 1

        assessment = item.get(
            "review_assessment",
            {}
        )

        rec = safe_string(
            assessment.get(
                "recommendation",
                ""
            )
            if isinstance(
                assessment,
                dict
            )
            else ""
        )

        if not rec:
            rec = "UNKNOWN"

        recommendation[
            rec
        ] += 1

        if decision == "MANUAL_REVIEW":

            manual_review_items.append(
                item
            )

        duplicate_check = item.get(
            "duplicate_check",
            {}
        )

        if (
            isinstance(
                duplicate_check,
                dict
            )
            and duplicate_check.get(
                "is_duplicate_candidate",
                False
            )
        ):

            duplicate_items.append(
                item
            )

    return {
        "total_website_locations": len(
            items
        ),

        "original_classification": dict(
            sorted(
                original_classification.items(),
                key=lambda x: x[0],
            )
        ),

        "final_decision": dict(
            sorted(
                final_decision.items(),
                key=lambda x: safe_string(
                    x[0]
                ),
            )
        ),

        "review_recommendation": dict(
            sorted(
                recommendation.items(),
                key=lambda x: safe_string(
                    x[0]
                ),
            )
        ),

        "manual_review_count": len(
            manual_review_items
        ),

        "duplicate_candidate_count": len(
            duplicate_items
        ),
    }


# ============================================================================
# PRINT MANUAL REVIEW ITEMS
# ============================================================================

def print_manual_review_items(
    items
):
    """
    Print all items that still require
    human review.
    """

    print(
        "\n"
        + "=" * 80
    )

    print(
        "MANUAL REVIEW ITEMS"
    )

    print(
        "=" * 80
    )

    found = False

    for index, item in enumerate(
        items,
        start=1,
    ):

        if item.get(
            "final_decision"
        ) != "MANUAL_REVIEW":

            continue

        found = True

        website = item.get(
            "website",
            {}
        )

        crm = item.get(
            "crm"
        ) or {}

        assessment = item.get(
            "review_assessment",
            {}
        )

        website_name = safe_string(
            website.get(
                "name",
                ""
            )
        )

        crm_name = safe_string(
            crm.get(
                "name",
                "NO CRM ACCOUNT"
            )
        )

        reason = safe_string(
            assessment.get(
                "recommendation_reason",
                ""
            )
            if isinstance(
                assessment,
                dict
            )
            else ""
        )

        print(
            f"\n {index} "
            f"{website_name} "
            f"=> "
            f"{crm_name} "
            f"| MANUAL_REVIEW "
            f"| {reason}"
        )

    if not found:

        print(
            "\nNo manual review items."
        )


# ============================================================================
# PRINT DUPLICATES
# ============================================================================

def print_duplicate_items(
    items
):
    """
    Print CRM accounts used by multiple
    website locations.
    """

    print(
        "\n"
        + "=" * 80
    )

    print(
        "DUPLICATE CRM CANDIDATES"
    )

    print(
        "=" * 80
    )

    found = False

    for index, item in enumerate(
        items,
        start=1,
    ):

        duplicate = item.get(
            "duplicate_check",
            {}
        )

        if not duplicate.get(
            "is_duplicate_candidate",
            False
        ):
            continue

        found = True

        website = item.get(
            "website",
            {}
        )

        crm = item.get(
            "crm",
            {}
        )

        website_name = safe_string(
            website.get(
                "name",
                ""
            )
        )

        crm_name = safe_string(
            crm.get(
                "name",
                ""
            )
        )

        account_id = safe_string(
            duplicate.get(
                "crm_account_id",
                ""
            )
        )

        used_by = duplicate.get(
            "used_by",
            []
        )

        print(
            f"\n {index} "
            f"{website_name} "
            f"=> "
            f"{crm_name} "
            f"| {account_id} "
            f"| USED BY: {used_by}"
        )

    if not found:

        print(
            "\nNo duplicate CRM candidates detected."
        )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":

    print(
        "Loading review queue..."
    )

    data = load_json(
        REVIEW_QUEUE_FILE
    )

    queue = data.get(
        "items",
        []
    )

    # ------------------------------------------------------------------------
    # Detect duplicates BEFORE building final records
    # ------------------------------------------------------------------------

    duplicate_map = detect_duplicate_candidates(
        queue
    )

    # ------------------------------------------------------------------------
    # Build final records
    # ------------------------------------------------------------------------

    final_items = []

    for item in queue:

        final_items.append(
            build_final_item(
                item,
                duplicate_map,
            )
        )

    # ------------------------------------------------------------------------
    # Build summary
    # ------------------------------------------------------------------------

    summary = build_summary(
        final_items,
        duplicate_map,
    )

    # ------------------------------------------------------------------------
    # Build output
    # ------------------------------------------------------------------------

    output = {
        "summary": summary,

        "items": final_items,

        "crm_not_on_website": data.get(
            "crm_not_on_website",
            []
        ),

        "duplicate_crm_candidates": (
            duplicate_map
        ),
    }

    save_json(
        output,
        OUTPUT_FILE,
    )

    # =========================================================================
    # CONSOLE OUTPUT
    # =========================================================================

    print(
        "\n"
        + "=" * 80
    )

    print(
        "FINAL REVIEW SUMMARY"
    )

    print(
        "=" * 80
    )

    print(
        f"\nTotal website locations: "
        f"{summary['total_website_locations']}"
    )

    # ------------------------------------------------------------------------
    # Original classification
    # ------------------------------------------------------------------------

    print(
        "\nOriginal classification:"
    )

    for classification, count in sorted(
        summary[
            "original_classification"
        ].items(),
        key=lambda x: safe_string(
            x[0]
        ),
    ):

        print(
            f"  {classification}: "
            f"{count}"
        )

    # ------------------------------------------------------------------------
    # Final decision
    # ------------------------------------------------------------------------

    print(
        "\nFinal decision:"
    )

    for action, count in sorted(
        summary[
            "final_decision"
        ].items(),
        key=lambda x: safe_string(
            x[0]
        ),
    ):

        print(
            f"  {action}: "
            f"{count}"
        )

    # ------------------------------------------------------------------------
    # Review recommendation
    # ------------------------------------------------------------------------

    print(
        "\nReview recommendation:"
    )

    for recommendation, count in sorted(
        summary[
            "review_recommendation"
        ].items(),
        key=lambda x: safe_string(
            x[0]
        ),
    ):

        print(
            f"  {recommendation}: "
            f"{count}"
        )

    # ------------------------------------------------------------------------
    # Manual review
    # ------------------------------------------------------------------------

    print_manual_review_items(
        final_items
    )

    # ------------------------------------------------------------------------
    # Duplicate candidates
    # ------------------------------------------------------------------------

    print_duplicate_items(
        final_items
    )

    print(
        "\n"
        + "=" * 80
    )

    print(
        "FINAL REVIEW COMPLETED"
    )

    print(
        "=" * 80
    )

    print(
        f"\nOutput saved to:"
    )

    print(
        OUTPUT_FILE
    )