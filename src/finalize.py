import json
from pathlib import Path
from collections import Counter


# ============================================================================
# PATH CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "final_review.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "final_mapping.json"
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


def save_json(
    data,
    file_path,
):

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
# MANUAL DECISIONS
# ============================================================================

MANUAL_DECISIONS = {

    "Bellhaven Woods of Toledo": {
        "final_decision": "MATCH",

        "crm_account_id": "0014DHACE6WQU3RMM5",

        "decision_source": "MANUAL_REVIEW",

        "reviewer_note": (
            "Exact name, matching physical address, city, state, "
            "and phone number confirm the same facility. "
            "CRM address uses expanded street naming."
        ),
    },


    "Bellhaven of Zanesville": {
        "final_decision": "MATCH",

        "crm_account_id": "001H1JMVZWP46D5VUF",

        "decision_source": "MANUAL_REVIEW",

        "reviewer_note": (
            "Website and CRM have the same physical address, "
            "city, and state. The CRM uses the name "
            "'Cedar Trail of Zanesville', indicating a likely "
            "rebranding or ownership transition. The location "
            "evidence is sufficiently strong to confirm the match."
        ),
    },


    "Bellhaven of Ashtabula": {
        "final_decision": "MATCH",

        "crm_account_id": "001NXP9X46CWEPSLSV",

        "decision_source": "MANUAL_REVIEW",

        "reviewer_note": (
            "Exact name, city, state, and phone number match. "
            "The CRM contains a PO Box while the website contains "
            "the physical facility address, which is consistent "
            "with mailing-versus-location address differences."
        ),
    },


    "Bellhaven of Chesterton": {
        "final_decision": "MATCH",

        "crm_account_id": "0013NUZQHQUEZ8DXEG",

        "decision_source": "MANUAL_REVIEW",

        "reviewer_note": (
            "Exact physical address, city, state, and phone number "
            "match. The CRM uses the different facility name "
            "'Chesterton Senior Commons', indicating the same "
            "physical location under a different or legacy name."
        ),
    },
}


# ============================================================================
# HELPERS
# ============================================================================

def safe_string(value):

    if value is None:
        return ""

    return str(value).strip()


def get_website_name(item):

    website = item.get(
        "website",
        {}
    )

    return safe_string(
        website.get(
            "name",
            ""
        )
    )


def get_crm(item):

    crm = item.get(
        "crm"
    )

    if not isinstance(
        crm,
        dict
    ):
        return None

    return crm


# ============================================================================
# FINALIZE ITEM
# ============================================================================

def finalize_item(item):

    website = item.get(
        "website",
        {}
    )

    website_name = get_website_name(
        item
    )

    crm = get_crm(
        item
    )

    original_classification = safe_string(
        item.get(
            "original_classification",
            ""
        )
    )

    original_reason = safe_string(
        item.get(
            "original_reason",
            ""
        )
    )

    # ------------------------------------------------------------------------
    # CASE 1: Manual decision exists
    # ------------------------------------------------------------------------

    if website_name in MANUAL_DECISIONS:

        manual = MANUAL_DECISIONS[
            website_name
        ]

        manual_crm_id = manual.get(
            "crm_account_id"
        )

        # Safety check:
        # Make sure the manually selected CRM ID is the same
        # CRM candidate currently associated with this item.

        current_crm_id = ""

        if crm:

            current_crm_id = safe_string(
                crm.get(
                    "account_id",
                    ""
                )
            )

        if (
            current_crm_id
            and manual_crm_id
            != current_crm_id
        ):

            raise ValueError(
                "\nManual decision mismatch for "
                f"'{website_name}'.\n"
                f"Expected CRM ID: {manual_crm_id}\n"
                f"Current candidate: {current_crm_id}\n"
                "Please verify the mapping before continuing."
            )

        final_decision = manual[
            "final_decision"
        ]

        decision_source = manual[
            "decision_source"
        ]

        reviewer_note = manual[
            "reviewer_note"
        ]

    # ------------------------------------------------------------------------
    # CASE 2: Existing automated final decision
    # ------------------------------------------------------------------------

    else:

        final_decision = safe_string(
            item.get(
                "final_decision",
                ""
            )
        )

        if not final_decision:

            final_decision = (
                "PENDING"
            )

        decision_source = (
            "AUTOMATED_REVIEW"
        )

        reviewer_note = ""

    # ------------------------------------------------------------------------
    # Determine CRM mapping
    # ------------------------------------------------------------------------

    crm_account_id = None

    if (
        final_decision == "MATCH"
        and crm
    ):

        crm_account_id = safe_string(
            crm.get(
                "account_id",
                ""
            )
        )

    # ------------------------------------------------------------------------
    # Build final record
    # ------------------------------------------------------------------------

    return {

        "website": website,

        "crm": crm,

        "mapping": {
            "crm_account_id": (
                crm_account_id
            ),

            "final_decision": (
                final_decision
            ),

            "decision_source": (
                decision_source
            ),

            "reviewer_note": (
                reviewer_note
            ),
        },

        "audit": {

            "original_classification": (
                original_classification
            ),

            "original_reason": (
                original_reason
            ),

            "review_recommendation": safe_string(
                item.get(
                    "review_assessment",
                    {}
                ).get(
                    "recommendation",
                    ""
                )
                if isinstance(
                    item.get(
                        "review_assessment",
                        {}
                    ),
                    dict
                )
                else ""
            ),

            "original_score": (
                item.get(
                    "original_evidence",
                    {}
                ).get(
                    "score"
                )
                if isinstance(
                    item.get(
                        "original_evidence",
                        {}
                    ),
                    dict
                )
                else None
            ),
        },
    }


# ============================================================================
# BUILD FINAL MAPPING
# ============================================================================

def build_final_mapping(data):

    items = data.get(
        "items",
        []
    )

    final_items = []

    for item in items:

        final_items.append(
            finalize_item(
                item
            )
        )

    return final_items


# ============================================================================
# VALIDATION
# ============================================================================

def validate_final_items(
    items
):
    """
    Validate the final mapping before saving.

    The goal is to prevent accidental duplicate CRM
    assignments among MATCH records.
    """

    crm_usage = {}

    errors = []

    for item in items:

        mapping = item.get(
            "mapping",
            {}
        )

        decision = safe_string(
            mapping.get(
                "final_decision",
                ""
            )
        )

        crm_id = safe_string(
            mapping.get(
                "crm_account_id",
                ""
            )
        )

        website_name = get_website_name(
            item
        )

        if decision == "MATCH":

            if not crm_id:

                errors.append(
                    f"{website_name}: MATCH without CRM account ID."
                )

                continue

            crm_usage.setdefault(
                crm_id,
                []
            ).append(
                website_name
            )

    # ------------------------------------------------------------------------
    # Detect duplicate CRM assignments
    # ------------------------------------------------------------------------

    for crm_id, websites in crm_usage.items():

        if len(websites) > 1:

            errors.append(
                f"CRM account {crm_id} is mapped to multiple "
                f"website locations: {websites}"
            )

    if errors:

        print(
            "\nVALIDATION ERRORS:"
        )

        for error in errors:

            print(
                f"  - {error}"
            )

        raise ValueError(
            "Final mapping validation failed."
        )

    return True


# ============================================================================
# SUMMARY
# ============================================================================

def build_summary(
    items,
    crm_not_on_website,
):

    final_decisions = Counter()

    decision_sources = Counter()

    original_classifications = Counter()

    matched_crm_ids = set()

    manual_decisions = 0

    automated_decisions = 0

    for item in items:

        mapping = item.get(
            "mapping",
            {}
        )

        decision = safe_string(
            mapping.get(
                "final_decision",
                ""
            )
        )

        source = safe_string(
            mapping.get(
                "decision_source",
                ""
            )
        )

        original = safe_string(
            item.get(
                "audit",
                {}
            ).get(
                "original_classification",
                ""
            )
            if isinstance(
                item.get(
                    "audit",
                    {}
                ),
                dict
            )
            else ""
        )

        if not decision:

            decision = "UNKNOWN"

        if not source:

            source = "UNKNOWN"

        if not original:

            original = "UNKNOWN"

        final_decisions[
            decision
        ] += 1

        decision_sources[
            source
        ] += 1

        original_classifications[
            original
        ] += 1

        if source == "MANUAL_REVIEW":

            manual_decisions += 1

        else:

            automated_decisions += 1

        crm_id = safe_string(
            mapping.get(
                "crm_account_id",
                ""
            )
        )

        if (
            decision == "MATCH"
            and crm_id
        ):

            matched_crm_ids.add(
                crm_id
            )

    return {

        "total_website_locations": len(
            items
        ),

        "final_decisions": dict(
            sorted(
                final_decisions.items()
            )
        ),

        "decision_sources": dict(
            sorted(
                decision_sources.items()
            )
        ),

        "original_classifications": dict(
            sorted(
                original_classifications.items()
            )
        ),

        "matched_crm_accounts": len(
            matched_crm_ids
        ),

        "crm_not_on_website": len(
            crm_not_on_website
        ),

        "manual_decisions": (
            manual_decisions
        ),

        "automated_decisions": (
            automated_decisions
        ),
    }


# ============================================================================
# PRINT FINAL RESULTS
# ============================================================================

def print_final_results(
    items
):

    print(
        "\n"
        + "=" * 80
    )

    print(
        "FINAL CRM MAPPING"
    )

    print(
        "=" * 80
    )

    for index, item in enumerate(
        items,
        start=1,
    ):

        website = item.get(
            "website",
            {}
        )

        crm = item.get(
            "crm"
        ) or {}

        mapping = item.get(
            "mapping",
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

        crm_id = safe_string(
            mapping.get(
                "crm_account_id",
                ""
            )
        )

        decision = safe_string(
            mapping.get(
                "final_decision",
                ""
            )
        )

        source = safe_string(
            mapping.get(
                "decision_source",
                ""
            )
        )

        if not crm_name:

            crm_name = "NONE"

        if not crm_id:

            crm_id = "NONE"

        print(
            f"\n{index}. "
            f"{website_name}"
        )

        print(
            f"   CRM: {crm_name}"
        )

        print(
            f"   CRM ID: {crm_id}"
        )

        print(
            f"   Decision: {decision}"
        )

        print(
            f"   Source: {source}"
        )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":

    print(
        "Loading final review..."
    )

    data = load_json(
        INPUT_FILE
    )

    # ------------------------------------------------------------------------
    # Build final mapping
    # ------------------------------------------------------------------------

    final_items = build_final_mapping(
        data
    )

    # ------------------------------------------------------------------------
    # Validate
    # ------------------------------------------------------------------------

    print(
        "\nValidating final mapping..."
    )

    validate_final_items(
        final_items
    )

    print(
        "Validation passed."
    )

    # ------------------------------------------------------------------------
    # CRM not on website
    # ------------------------------------------------------------------------

    crm_not_on_website = data.get(
        "crm_not_on_website",
        []
    )

    # ------------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------------

    summary = build_summary(
        final_items,
        crm_not_on_website,
    )

    # ------------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------------

    output = {

        "summary": summary,

        "items": final_items,

        "crm_not_on_website": (
            crm_not_on_website
        ),

        "manual_decisions": (
            MANUAL_DECISIONS
        ),
    }

    save_json(
        output,
        OUTPUT_FILE,
    )

    # ------------------------------------------------------------------------
    # Console
    # ------------------------------------------------------------------------

    print(
        "\n"
        + "=" * 80
    )

    print(
        "FINALIZATION SUMMARY"
    )

    print(
        "=" * 80
    )

    print(
        f"\nTotal website locations: "
        f"{summary['total_website_locations']}"
    )

    print(
        "\nFinal decisions:"
    )

    for decision, count in sorted(
        summary[
            "final_decisions"
        ].items()
    ):

        print(
            f"  {decision}: {count}"
        )

    print(
        "\nDecision sources:"
    )

    for source, count in sorted(
        summary[
            "decision_sources"
        ].items()
    ):

        print(
            f"  {source}: {count}"
        )

    print(
        f"\nMatched CRM accounts: "
        f"{summary['matched_crm_accounts']}"
    )

    print(
        f"CRM accounts not on website: "
        f"{summary['crm_not_on_website']}"
    )

    print(
        "\n"
        + "=" * 80
    )

    print(
        "FINAL MAPPING CREATED"
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

    print(
        "\nFinalization completed successfully."
    )