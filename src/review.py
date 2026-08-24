import json
import re
from pathlib import Path
from collections import defaultdict


# ============================================================================
# PATH CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CLASSIFIED_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "classified_matches.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "review_queue.json"
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
# NORMALIZATION
# ============================================================================

def normalize_text(value):

    if value is None:
        return ""

    value = str(value).strip().lower()

    value = re.sub(
        r"[,\.\(\)\-/]",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def normalize_address(value):
    """
    Normalize common US address variations.

    Examples:

        980 W Michigan Ave
        980 West Michigan Avenue

    become equivalent.
    """

    value = normalize_text(value)

    if not value:
        return ""

    replacements = {
        r"\bwest\b": "w",
        r"\beast\b": "e",
        r"\bnorth\b": "n",
        r"\bsouth\b": "s",

        r"\bavenue\b": "ave",
        r"\bstreet\b": "st",
        r"\broad\b": "rd",
        r"\bdrive\b": "dr",
        r"\bboulevard\b": "blvd",
        r"\blane\b": "ln",
        r"\bcourt\b": "ct",
        r"\bplace\b": "pl",
        r"\bparkway\b": "pkwy",
        r"\bhighway\b": "hwy",
        r"\bterrace\b": "ter",
        r"\bcircle\b": "cir",
    }

    for pattern, replacement in replacements.items():

        value = re.sub(
            pattern,
            replacement,
            value,
        )

    value = re.sub(
        r"[^a-z0-9\s]",
        "",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def normalize_phone(value):

    if value is None:
        return ""

    return re.sub(
        r"\D",
        "",
        str(value),
    )


def normalize_zip(value):

    if value is None:
        return ""

    value = str(value).strip()

    if not value:
        return ""

    return re.sub(
        r"\s+",
        "",
        value,
    )


# ============================================================================
# FIELD COMPARISON
# ============================================================================

def compare_field(
    website_value,
    crm_value,
    field_type="text",
):
    """
    Return:

        MATCH
        MISMATCH
        UNKNOWN

    Missing website information is UNKNOWN,
    not MISMATCH.
    """

    if field_type == "address":

        website_norm = normalize_address(
            website_value
        )

        crm_norm = normalize_address(
            crm_value
        )

    elif field_type == "phone":

        website_norm = normalize_phone(
            website_value
        )

        crm_norm = normalize_phone(
            crm_value
        )

    elif field_type == "zip":

        website_norm = normalize_zip(
            website_value
        )

        crm_norm = normalize_zip(
            crm_value
        )

    else:

        website_norm = normalize_text(
            website_value
        )

        crm_norm = normalize_text(
            crm_value
        )

    if not website_norm and not crm_norm:
        return "UNKNOWN"

    if not website_norm:
        return "UNKNOWN"

    if not crm_norm:
        return "UNKNOWN"

    if website_norm == crm_norm:
        return "MATCH"

    return "MISMATCH"


# ============================================================================
# NAME SIMILARITY
# ============================================================================

def get_name_similarity(evidence):

    value = evidence.get(
        "name_similarity",
        0,
    )

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return 0.0


# ============================================================================
# DUPLICATE CANDIDATE DETECTION
# ============================================================================

def build_candidate_usage(data):
    """
    Detect CRM accounts that are selected as best candidates
    for more than one website location.

    IMPORTANT:

    NO_CRM_ACCOUNT items are excluded from duplicate detection.

    This prevents low-confidence fallback candidates from being
    incorrectly treated as real CRM matches.
    """

    usage = defaultdict(list)

    for item in data.get(
        "matches",
        [],
    ):

        classification = item.get(
            "classification",
            "",
        )

        # ------------------------------------------------------------
        # IMPORTANT:
        # Do not use NO_CRM_ACCOUNT fallback candidates.
        # ------------------------------------------------------------

        if classification == "NO_CRM_ACCOUNT":
            continue

        candidate = item.get(
            "best_candidate"
        )

        if candidate is None:
            continue

        crm_account_id = candidate.get(
            "crm_account_id"
        )

        website = item.get(
            "website",
            {}
        )

        website_name = website.get(
            "name",
            ""
        )

        if not crm_account_id:
            continue

        usage[
            crm_account_id
        ].append(
            website_name
        )

    return {
        account_id: names
        for account_id, names in usage.items()
        if len(names) > 1
    }


# ============================================================================
# SECONDARY MATCH ASSESSMENT
# ============================================================================

def assess_match(
    website,
    crm,
    evidence,
    duplicate_usage=None,
):
    """
    Perform secondary match assessment.

    Rules:

    1. Duplicate candidate -> MANUAL_REVIEW
    2. Exact/strong name + location -> CONFIDENT_MATCH
    3. Location + phone -> CONFIDENT_MATCH
    4. Location + reasonable name -> LIKELY_MATCH
    5. Location only -> MANUAL_REVIEW
    6. Otherwise -> MANUAL_REVIEW
    """

    duplicate_usage = duplicate_usage or []

    name_similarity = get_name_similarity(
        evidence
    )

    # ------------------------------------------------------------------------
    # FIELD STATUS
    # ------------------------------------------------------------------------

    name_status = "MISMATCH"

    if name_similarity >= 95:

        name_status = "MATCH"

    elif name_similarity >= 80:

        name_status = "LIKELY_MATCH"

    address_status = compare_field(
        website.get(
            "address",
            ""
        ),
        crm.get(
            "address",
            ""
        ),
        "address",
    )

    city_status = compare_field(
        website.get(
            "city",
            ""
        ),
        crm.get(
            "city",
            ""
        ),
        "text",
    )

    state_status = compare_field(
        website.get(
            "state",
            ""
        ),
        crm.get(
            "state",
            ""
        ),
        "text",
    )

    zip_status = compare_field(
        website.get(
            "zip_code",
            ""
        ),
        crm.get(
            "zip",
            ""
        ),
        "zip",
    )

    phone_status = compare_field(
        website.get(
            "phone",
            ""
        ),
        crm.get(
            "phone",
            ""
        ),
        "phone",
    )

    # ------------------------------------------------------------------------
    # LOCATION MATCH
    # ------------------------------------------------------------------------

    strong_location_match = (
        address_status == "MATCH"
        and city_status == "MATCH"
        and state_status == "MATCH"
    )

    exact_name_and_location = (
        name_similarity >= 95
        and strong_location_match
    )

    strong_name_location_match = (
        name_similarity >= 90
        and strong_location_match
    )

    # ------------------------------------------------------------------------
    # DUPLICATE RULE
    # ------------------------------------------------------------------------

    if duplicate_usage:

        recommendation = "MANUAL_REVIEW"

        recommendation_reason = (
            "The CRM candidate appears as the best "
            "match for multiple website locations. "
            "Manual review is required to confirm "
            "whether the CRM account is duplicated "
            "or incorrectly reused."
        )

    # ------------------------------------------------------------------------
    # EXACT NAME + LOCATION
    # ------------------------------------------------------------------------

    elif exact_name_and_location:

        recommendation = "CONFIDENT_MATCH"

        recommendation_reason = (
            "Exact or near-exact name with matching "
            "normalized address, city, and state."
        )

    # ------------------------------------------------------------------------
    # STRONG NAME + LOCATION
    # ------------------------------------------------------------------------

    elif strong_name_location_match:

        recommendation = "CONFIDENT_MATCH"

        recommendation_reason = (
            "Strong name similarity with matching "
            "normalized address, city, and state."
        )

    # ------------------------------------------------------------------------
    # LOCATION + PHONE
    # ------------------------------------------------------------------------

    elif (
        strong_location_match
        and phone_status == "MATCH"
    ):

        recommendation = "CONFIDENT_MATCH"

        recommendation_reason = (
            "Address, city, state, and phone match "
            "even though the CRM name differs."
        )

    # ------------------------------------------------------------------------
    # LOCATION + NAME
    # ------------------------------------------------------------------------

    elif (
        strong_location_match
        and name_similarity >= 80
    ):

        recommendation = "LIKELY_MATCH"

        recommendation_reason = (
            "Location matches and the names are "
            "strongly similar."
        )

    # ------------------------------------------------------------------------
    # LOCATION ONLY
    # ------------------------------------------------------------------------

    elif strong_location_match:

        recommendation = "MANUAL_REVIEW"

        recommendation_reason = (
            "Location matches, but name evidence "
            "requires manual confirmation."
        )

    # ------------------------------------------------------------------------
    # INSUFFICIENT EVIDENCE
    # ------------------------------------------------------------------------

    else:

        recommendation = "MANUAL_REVIEW"

        recommendation_reason = (
            "Insufficient evidence for an automatic "
            "confident match."
        )

    return {
        "recommendation": recommendation,

        "recommendation_reason": (
            recommendation_reason
        ),

        "field_status": {
            "name": name_status,
            "address": address_status,
            "city": city_status,
            "state": state_status,
            "zip": zip_status,
            "phone": phone_status,
        },

        "duplicate_candidate": bool(
            duplicate_usage
        ),

        "duplicate_used_by": (
            duplicate_usage
            if duplicate_usage
            else []
        ),

        "normalized_values": {
            "website_address": normalize_address(
                website.get(
                    "address",
                    ""
                )
            ),

            "crm_address": normalize_address(
                crm.get(
                    "address",
                    ""
                )
            ),

            "website_phone": normalize_phone(
                website.get(
                    "phone",
                    ""
                )
            ),

            "crm_phone": normalize_phone(
                crm.get(
                    "phone",
                    ""
                )
            ),

            "website_zip": normalize_zip(
                website.get(
                    "zip_code",
                    ""
                )
            ),

            "crm_zip": normalize_zip(
                crm.get(
                    "zip",
                    ""
                )
            ),
        },
    }


# ============================================================================
# WEBSITE CLEANER
# ============================================================================

def clean_website(website):

    return {
        "name": website.get(
            "name",
            ""
        ),

        "address": website.get(
            "address",
            ""
        ),

        "city": website.get(
            "city",
            ""
        ),

        "state": website.get(
            "state",
            ""
        ),

        "zip_code": website.get(
            "zip_code",
            website.get(
                "zip",
                ""
            ),
        ),

        "phone": website.get(
            "phone",
            ""
        ),

        "care_offerings": website.get(
            "care_offerings",
            []
        ),

        "source_url": website.get(
            "source_url",
            ""
        ),
    }


# ============================================================================
# CRM CLEANER
# ============================================================================

def clean_crm(candidate):

    return {
        "account_id": candidate.get(
            "crm_account_id",
            ""
        ),

        "name": candidate.get(
            "crm_name",
            ""
        ),

        "parent": candidate.get(
            "crm_parent",
            ""
        ),

        "address": candidate.get(
            "crm_address",
            ""
        ),

        "city": candidate.get(
            "crm_city",
            ""
        ),

        "state": candidate.get(
            "crm_state",
            ""
        ),

        "zip": candidate.get(
            "crm_zip",
            ""
        ),

        "phone": candidate.get(
            "crm_phone",
            ""
        ),

        "status": candidate.get(
            "crm_status",
            ""
        ),

        "lifetime_revenue": candidate.get(
            "lifetime_revenue",
            0
        ),

        "outstanding_ar": candidate.get(
            "outstanding_ar",
            0
        ),

        "chow_current_account": candidate.get(
            "chow_current_account",
            ""
        ),

        "duplicate_of_account": candidate.get(
            "duplicate_of_account",
            ""
        ),
    }


# ============================================================================
# BUILD REVIEW ITEM
# ============================================================================

def build_review_item(
    item,
    duplicate_usage,
):
    """
    Convert classified match into reviewer-friendly record.

    IMPORTANT:

    NO_CRM_ACCOUNT is treated as a terminal classification.

    Even if classified_matches.json contains a weak best_candidate,
    it will NOT be promoted into MANUAL_REVIEW or duplicate detection.
    """

    classification = item.get(
        "classification",
        "",
    )

    website_raw = item.get(
        "website",
        {}
    )

    website = clean_website(
        website_raw
    )

    candidate = item.get(
        "best_candidate"
    )

    # ========================================================================
    # IMPORTANT: NO_CRM_ACCOUNT
    # ========================================================================

    if classification == "NO_CRM_ACCOUNT":

        return {
            "classification": classification,

            "reason": item.get(
                "reason",
                ""
            ),

            "website": website,

            "crm": None,

            "evidence": None,

            "review_assessment": {
                "recommendation": "NO_CRM_ACCOUNT",

                "recommendation_reason": (
                    "The original matching engine "
                    "classified this website location "
                    "as having no sufficiently reliable "
                    "CRM account."
                ),

                "field_status": {},

                "duplicate_candidate": False,

                "duplicate_used_by": [],

                "normalized_values": {},
            },

            "decision": {
                "status": "PENDING",
                "action": None,
                "reviewer_note": "",
            },
        }

    # ========================================================================
    # NO CANDIDATE
    # ========================================================================

    if candidate is None:

        return {
            "classification": classification,

            "reason": item.get(
                "reason",
                ""
            ),

            "website": website,

            "crm": None,

            "evidence": None,

            "review_assessment": {
                "recommendation": "MANUAL_REVIEW",

                "recommendation_reason": (
                    "No CRM candidate was supplied "
                    "for a classification that requires "
                    "additional review."
                ),

                "field_status": {},

                "duplicate_candidate": False,

                "duplicate_used_by": [],

                "normalized_values": {},
            },

            "decision": {
                "status": "PENDING",
                "action": None,
                "reviewer_note": "",
            },
        }

    # ========================================================================
    # CRM CANDIDATE
    # ========================================================================

    evidence = candidate.get(
        "evidence",
        {}
    )

    crm = clean_crm(
        candidate
    )

    crm_account_id = crm.get(
        "account_id",
        ""
    )

    duplicate_used_by = duplicate_usage.get(
        crm_account_id,
        [],
    )

    review_assessment = assess_match(
        website,
        crm,
        evidence,
        duplicate_used_by,
    )

    return {
        # --------------------------------------------------------------------
        # Original classifier
        # --------------------------------------------------------------------

        "classification": classification,

        "reason": item.get(
            "reason",
            ""
        ),

        # --------------------------------------------------------------------
        # Website
        # --------------------------------------------------------------------

        "website": website,

        # --------------------------------------------------------------------
        # CRM
        # --------------------------------------------------------------------

        "crm": crm,

        # --------------------------------------------------------------------
        # Original evidence
        # --------------------------------------------------------------------

        "evidence": {
            "score": evidence.get(
                "score",
                candidate.get(
                    "score",
                    0
                ),
            ),

            "name_similarity": evidence.get(
                "name_similarity",
                0
            ),

            "address_match": evidence.get(
                "address_match",
                False
            ),

            "city_match": evidence.get(
                "city_match",
                False
            ),

            "state_match": evidence.get(
                "state_match",
                False
            ),

            "zip_match": evidence.get(
                "zip_match",
                False
            ),

            "phone_match": evidence.get(
                "phone_match",
                False
            ),
        },

        # --------------------------------------------------------------------
        # Secondary assessment
        # --------------------------------------------------------------------

        "review_assessment": review_assessment,

        # --------------------------------------------------------------------
        # Human decision
        # --------------------------------------------------------------------

        "decision": {
            "status": "PENDING",
            "action": None,
            "reviewer_note": "",
        },
    }


# ============================================================================
# BUILD REVIEW QUEUE
# ============================================================================

def build_review_queue(
    data,
    duplicate_usage,
):

    queue = []

    for item in data.get(
        "matches",
        []
    ):

        queue.append(
            build_review_item(
                item,
                duplicate_usage,
            )
        )

    return queue


# ============================================================================
# SUMMARY
# ============================================================================

def build_summary(
    queue,
    duplicate_usage,
):

    classification_counts = {}

    recommendation_counts = {}

    duplicate_item_count = 0

    for item in queue:

        # --------------------------------------------------------------------
        # Original classification
        # --------------------------------------------------------------------

        classification = item.get(
            "classification",
            "UNKNOWN"
        )

        classification_counts[
            classification
        ] = (
            classification_counts.get(
                classification,
                0
            )
            + 1
        )

        # --------------------------------------------------------------------
        # Secondary recommendation
        # --------------------------------------------------------------------

        assessment = item.get(
            "review_assessment",
            {}
        )

        recommendation = assessment.get(
            "recommendation",
            "UNKNOWN"
        )

        recommendation_counts[
            recommendation
        ] = (
            recommendation_counts.get(
                recommendation,
                0
            )
            + 1
        )

        # --------------------------------------------------------------------
        # Duplicate affected item
        # --------------------------------------------------------------------

        if assessment.get(
            "duplicate_candidate",
            False
        ):

            duplicate_item_count += 1

    return {
        "total": len(queue),

        "pending": len(queue),

        "by_classification": (
            classification_counts
        ),

        "by_review_recommendation": (
            recommendation_counts
        ),

        "duplicate_candidate_items": (
            duplicate_item_count
        ),

        "duplicate_crm_accounts": len(
            duplicate_usage
        ),
    }


# ============================================================================
# MANUAL REVIEW REPORT
# ============================================================================

def print_manual_review_report(queue):

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

    manual_count = 0

    for index, item in enumerate(
        queue,
        start=1
    ):

        assessment = item.get(
            "review_assessment",
            {}
        )

        if assessment.get(
            "recommendation"
        ) != "MANUAL_REVIEW":

            continue

        website = item.get(
            "website",
            {}
        )

        crm = item.get(
            "crm"
        )

        website_name = website.get(
            "name",
            ""
        )

        crm_name = ""

        if crm:
            crm_name = crm.get(
                "name",
                ""
            )

        reason = assessment.get(
            "recommendation_reason",
            ""
        )

        print(
            f"\n {index} "
            f"{website_name} => "
            f"{crm_name} | "
            f"MANUAL_REVIEW | "
            f"{reason}"
        )

        manual_count += 1

    if manual_count == 0:

        print(
            "\nNo manual review items."
        )

    return manual_count


# ============================================================================
# DUPLICATE REPORT
# ============================================================================

def print_duplicate_report(queue):

    duplicate_items = 0

    for index, item in enumerate(
        queue,
        start=1
    ):

        assessment = item.get(
            "review_assessment",
            {}
        )

        if not assessment.get(
            "duplicate_candidate",
            False
        ):

            continue

        website = item.get(
            "website",
            {}
        )

        crm = item.get(
            "crm"
        )

        if not crm:
            continue

        website_name = website.get(
            "name",
            ""
        )

        crm_name = crm.get(
            "name",
            ""
        )

        account_id = crm.get(
            "account_id",
            ""
        )

        used_by = assessment.get(
            "duplicate_used_by",
            []
        )

        print(
            f"\n {index} "
            f"{website_name} => "
            f"{crm_name} | "
            f"{account_id} | "
            f"USED BY: {used_by}"
        )

        duplicate_items += 1

    print(
        f"\nDuplicate candidate items: "
        f"{duplicate_items}"
    )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":

    print(
        "Loading classified matches..."
    )

    data = load_json(
        CLASSIFIED_FILE
    )

    # ------------------------------------------------------------------------
    # Detect duplicate CRM candidates
    #
    # IMPORTANT:
    # NO_CRM_ACCOUNT items are excluded inside this function.
    # ------------------------------------------------------------------------

    duplicate_usage = build_candidate_usage(
        data
    )

    # ------------------------------------------------------------------------
    # Build review queue
    # ------------------------------------------------------------------------

    queue = build_review_queue(
        data,
        duplicate_usage,
    )

    # ------------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------------

    summary = build_summary(
        queue,
        duplicate_usage,
    )

    # ------------------------------------------------------------------------
    # Final output
    # ------------------------------------------------------------------------

    output = {
        "summary": summary,

        "items": queue,

        "crm_not_on_website": data.get(
            "crm_not_on_website",
            []
        ),

        "duplicate_crm_accounts": [
            {
                "crm_account_id": account_id,

                "used_by": website_names,
            }

            for account_id, website_names
            in duplicate_usage.items()
        ],
    }

    save_json(
        output,
        OUTPUT_FILE,
    )

    # ------------------------------------------------------------------------
    # Console summary
    # ------------------------------------------------------------------------

    print(
        "\nReview queue created:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        f"\nTotal review items: "
        f"{len(queue)}"
    )

    print(
        "\nOriginal classification:"
    )

    for classification, count in sorted(
        summary[
            "by_classification"
        ].items()
    ):

        print(
            f"  {classification}: "
            f"{count}"
        )

    print(
        "\nSecondary review assessment:"
    )

    for recommendation, count in sorted(
        summary[
            "by_review_recommendation"
        ].items()
    ):

        print(
            f"  {recommendation}: "
            f"{count}"
        )

    print(
        f"\nDuplicate candidate items: "
        f"{summary['duplicate_candidate_items']}"
    )

    # ------------------------------------------------------------------------
    # Detailed manual review report
    # ------------------------------------------------------------------------

    print_manual_review_report(
        queue
    )

    # ------------------------------------------------------------------------
    # Detailed duplicate report
    # ------------------------------------------------------------------------

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

    if duplicate_usage:

        print_duplicate_report(
            queue
        )

    else:

        print(
            "\nNo duplicate CRM candidates detected."
        )

    # ------------------------------------------------------------------------
    # Completed
    # ------------------------------------------------------------------------

    print(
        "\n"
        + "=" * 80
    )

    print(
        "REVIEW ASSESSMENT COMPLETED"
    )

    print(
        "=" * 80
    )