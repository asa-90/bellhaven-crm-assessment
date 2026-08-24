import hashlib
import json
from pathlib import Path

import streamlit as st

from src.api import CRMClient
from src.review_db import (
    initialize_db,
    get_decision,
    save_decision,
)


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "final_mapping.json"
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Bellhaven CRM Review",
    page_icon="🏥",
    layout="wide",
)


# ============================================================
# INITIALIZE REVIEW DATABASE
# ============================================================

initialize_db()


# ============================================================
# LOAD MATCHING RESULTS
# ============================================================

@st.cache_data
def load_mapping():

    if not DATA_FILE.exists():

        st.error(
            f"Matching result not found:\n\n"
            f"{DATA_FILE}"
        )

        st.stop()

    with open(
        DATA_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


data = load_mapping()

items = data.get(
    "items",
    [],
)


# ============================================================
# HELPERS
# ============================================================

def get_classification(item):

    audit = item.get(
        "audit",
        {},
    )

    return audit.get(
        "original_classification",
        item.get(
            "classification",
            "UNKNOWN",
        ),
    )


def make_proposal_id(item):
    """
    Create a deterministic proposal ID.

    Uses stable location identity rather than only
    the website name, so minor name changes do not
    automatically create a brand-new proposal.
    """

    website = item.get(
        "website",
        {},
    )

    crm = item.get(
        "crm"
    )

    crm_account_id = ""

    if crm:

        crm_account_id = crm.get(
            "account_id",
            "",
        )

    identity_parts = [
        website.get(
            "address",
            "",
        ).strip().lower(),

        website.get(
            "city",
            "",
        ).strip().lower(),

        website.get(
            "state",
            "",
        ).strip().lower(),

        website.get(
            "zip",
            website.get(
                "zip_code",
                "",
            ),
        ).strip().lower(),

        crm_account_id.strip().lower(),
    ]

    identity = "|".join(
        identity_parts
    )

    return hashlib.sha256(
        identity.encode(
            "utf-8"
        )
    ).hexdigest()


def format_value(value):

    if value is None:

        return ""

    if isinstance(
        value,
        list,
    ):

        return ", ".join(
            str(value_item)
            for value_item in value
        )

    return str(value)


def get_pending_items():

    pending = []

    for item in items:

        proposal_id = make_proposal_id(
            item
        )

        decision = get_decision(
            proposal_id
        )

        if decision is None:

            pending.append(
                item
            )

    return pending


# ============================================================
# PENDING QUEUE
# ============================================================

pending_items = get_pending_items()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    "## Review Queue"
)

st.sidebar.metric(
    "Total Proposals",
    len(items),
)

st.sidebar.metric(
    "Pending",
    len(pending_items),
)

st.sidebar.divider()


# ============================================================
# CATEGORY COUNTS
# ============================================================

category_counts = {}

for item in pending_items:

    category = get_classification(
        item
    )

    category_counts[category] = (
        category_counts.get(
            category,
            0,
        )
        + 1
    )


# ============================================================
# CATEGORY FILTER
# ============================================================

st.sidebar.markdown(
    "### Filter by Category"
)

available_categories = sorted(
    category_counts.keys()
)

filter_options = [
    "ALL"
] + available_categories


selected_category = st.sidebar.selectbox(
    "Category",
    filter_options,
    label_visibility="collapsed",
)


st.sidebar.divider()

if available_categories:

    st.sidebar.caption(
        "Pending by category"
    )

    for category in available_categories:

        st.sidebar.write(
            f"**{category}:** "
            f"{category_counts[category]}"
        )


st.sidebar.divider()

st.sidebar.caption(
    "CRM writes only happen after "
    "explicit reviewer approval."
)


# ============================================================
# APPLY FILTER
# ============================================================

if selected_category == "ALL":

    filtered_items = pending_items

else:

    filtered_items = [
        item
        for item in pending_items
        if get_classification(item)
        == selected_category
    ]


# ============================================================
# HEADER
# ============================================================

st.title(
    "Bellhaven CRM Review"
)

st.caption(
    "Review proposed CRM changes before "
    "they are written back to the CRM."
)


if selected_category == "ALL":

    st.info(
        f"Showing all pending proposals: "
        f"{len(filtered_items)}"
    )

else:

    st.info(
        f"Showing {selected_category}: "
        f"{len(filtered_items)} proposal(s)"
    )


# ============================================================
# EMPTY QUEUE
# ============================================================

if not pending_items:

    st.success(
        "All proposals have been reviewed."
    )

    st.stop()


if not filtered_items:

    st.warning(
        f"No pending proposals in category "
        f"'{selected_category}'."
    )

    st.stop()


# ============================================================
# PROPOSAL SELECTOR
# ============================================================

st.markdown(
    "**Proposal**"
)

proposal_labels = []

for index, item in enumerate(
    filtered_items
):

    website = item.get(
        "website",
        {},
    )

    classification = get_classification(
        item
    )

    website_name = website.get(
        "name",
        "Unknown Location",
    )

    proposal_labels.append(
        f"{index + 1}. "
        f"{website_name} "
        f"[{classification}]"
    )


selected_label = st.selectbox(
    "Select proposal",
    proposal_labels,
    label_visibility="collapsed",
)


selected_index = proposal_labels.index(
    selected_label
)

item = filtered_items[
    selected_index
]


# ============================================================
# DATA EXTRACTION
# ============================================================

website = item.get(
    "website",
    {},
)

crm = item.get(
    "crm"
)

audit = item.get(
    "audit",
    {}
)

classification = get_classification(
    item
)

reason = audit.get(
    "original_reason",
    item.get(
        "reason",
        "",
    ),
)

match_score = audit.get(
    "original_score",
    item.get(
        "match_score"
    ),
)

crm_account_id = ""

if crm:

    crm_account_id = crm.get(
        "account_id",
        "",
    )


# ============================================================
# SUMMARY
# ============================================================

st.divider()

st.markdown(
    f"### {website.get('name', 'Unknown Location')}"
)

summary_col1, summary_col2, summary_col3 = st.columns(
    [1.2, 1, 2.5]
)


with summary_col1:

    st.caption(
        "CLASSIFICATION"
    )

    st.markdown(
        f"**{classification}**"
    )


with summary_col2:

    st.caption(
        "MATCH SCORE"
    )

    if match_score is not None:

        st.markdown(
            f"**{match_score}**"
        )

    else:

        st.markdown(
            "**N/A**"
        )


with summary_col3:

    st.caption(
        "CRM ACCOUNT"
    )

    if crm_account_id:

        st.code(
            crm_account_id,
            language=None,
        )

    else:

        st.markdown(
            "**NO CRM ACCOUNT**"
        )


if reason:

    st.info(
        reason
    )


# ============================================================
# SUPPORTING EVIDENCE
# ============================================================

st.divider()

st.markdown(
    "## Supporting Evidence"
)

website_col, crm_col = st.columns(
    [1, 1]
)


# ============================================================
# WEBSITE DATA
# ============================================================

with website_col:

    st.markdown(
        "### 🌐 Website Data"
    )

    website_data = {
        "Name": website.get(
            "name"
        ),
        "Address": website.get(
            "address"
        ),
        "City": website.get(
            "city"
        ),
        "State": website.get(
            "state"
        ),
        "ZIP": website.get(
            "zip",
            website.get(
                "zip_code"
            ),
        ),
        "Phone": website.get(
            "phone"
        ),
        "Care Offerings": website.get(
            "care_offerings"
        ),
    }

    for label, value in website_data.items():

        st.write(
            f"**{label}:** "
            f"{format_value(value)}"
        )

    source_url = website.get(
        "source_url"
    )

    if source_url:

        st.link_button(
            "Open Website Source",
            source_url,
        )


# ============================================================
# CRM DATA
# ============================================================

with crm_col:

    st.markdown(
        "### 🏢 CRM Data"
    )

    if crm:

        crm_data = {
            "Account ID": crm.get(
                "account_id"
            ),
            "Name": crm.get(
                "name"
            ),
            "Parent": (
                crm.get(
                    "parent_name"
                )
                or crm.get(
                    "parent"
                )
            ),
            "Address": crm.get(
                "billing_street",
                crm.get(
                    "address"
                ),
            ),
            "City": crm.get(
                "billing_city",
                crm.get(
                    "city"
                ),
            ),
            "State": crm.get(
                "billing_state",
                crm.get(
                    "state"
                ),
            ),
            "ZIP": crm.get(
                "billing_zip",
                crm.get(
                    "zip"
                ),
            ),
            "Phone": crm.get(
                "phone"
            ),
            "Status": crm.get(
                "status"
            ),
        }

        for label, value in crm_data.items():

            st.write(
                f"**{label}:** "
                f"{format_value(value)}"
            )

    else:

        st.warning(
            "No CRM account was identified."
        )


# ============================================================
# PROPOSED CRM CHANGE
# ============================================================

st.divider()

st.markdown(
    "## Proposed CRM Change"
)

proposed_changes = {}

proposed_create = {}


# ============================================================
# NO CRM ACCOUNT
# ============================================================

if classification == "NO_CRM_ACCOUNT":

    care_offerings = website.get(
        "care_offerings",
        [],
    )

    care_type = ""

    if care_offerings:

        care_type = care_offerings[0]


    proposed_create = {
        "name": website.get(
            "name",
            "",
        ),
        "billing_street": website.get(
            "address",
            "",
        ),
        "billing_city": website.get(
            "city",
            "",
        ),
        "billing_state": website.get(
            "state",
            "",
        ),
        "billing_zip": website.get(
            "zip",
            website.get(
                "zip_code",
                "",
            ),
        ),
        "care_type": care_type,
        "status": "Active",
        "phone": website.get(
            "phone",
            "",
        ),
    }


    st.markdown(
        "**New CRM Account will be created:**"
    )

    st.json(
        proposed_create
    )


# ============================================================
# EXISTING CRM ACCOUNT
# ============================================================

elif crm:

    crm_name = crm.get(
        "name",
        "",
    )

    website_name = website.get(
        "name",
        "",
    )

    if website_name and (
        website_name
        != crm_name
    ):

        proposed_changes[
            "name"
        ] = website_name


    website_address = website.get(
        "address",
        "",
    )

    crm_address = crm.get(
        "billing_street",
        crm.get(
            "address",
            "",
        ),
    )

    if website_address and (
        website_address
        != crm_address
    ):

        proposed_changes[
            "billing_street"
        ] = website_address


    website_city = website.get(
        "city",
        "",
    )

    crm_city = crm.get(
        "billing_city",
        crm.get(
            "city",
            "",
        ),
    )

    if website_city and (
        website_city
        != crm_city
    ):

        proposed_changes[
            "billing_city"
        ] = website_city


    website_state = website.get(
        "state",
        "",
    )

    crm_state = crm.get(
        "billing_state",
        crm.get(
            "state",
            "",
        ),
    )

    if website_state and (
        website_state
        != crm_state
    ):

        proposed_changes[
            "billing_state"
        ] = website_state


    website_zip = website.get(
        "zip",
        website.get(
            "zip_code",
            "",
        ),
    )

    crm_zip = crm.get(
        "billing_zip",
        crm.get(
            "zip",
            "",
        ),
    )

    if website_zip and (
        website_zip
        != crm_zip
    ):

        proposed_changes[
            "billing_zip"
        ] = website_zip


    website_phone = website.get(
        "phone",
        "",
    )

    crm_phone = crm.get(
        "phone",
        "",
    )

    if website_phone and (
        website_phone
        != crm_phone
    ):

        proposed_changes[
            "phone"
        ] = website_phone


    # ========================================================
    # DUPLICATE
    # ========================================================

    if classification == "DUPLICATE":

        duplicate_target = (
            item.get(
                "duplicate_of_account"
            )
            or audit.get(
                "duplicate_of_account"
            )
            or crm.get(
                "duplicate_of_account"
            )
        )


        if duplicate_target:

            proposed_changes = {
                "duplicate_of_account":
                    duplicate_target
            }


            st.markdown(
                "**Duplicate Account Action**"
            )

            st.write(
                "This CRM account will be marked "
                "as a duplicate of:"
            )

            st.code(
                duplicate_target,
                language=None,
            )

        else:

            st.warning(
                "This proposal is classified "
                "as DUPLICATE, but no target "
                "account ID was provided."
            )


    if (
        classification != "DUPLICATE"
        and proposed_changes
    ):

        st.json(
            proposed_changes
        )


    if (
        classification != "DUPLICATE"
        and not proposed_changes
    ):

        st.success(
            "No CRM field changes are proposed."
        )


# ============================================================
# UNKNOWN / NO AUTOMATED ACTION
# ============================================================

else:

    st.warning(
        "No automated CRM action is proposed "
        "for this record."
    )


# ============================================================
# REVIEW DECISION
# ============================================================

st.divider()

st.markdown(
    "## Reviewer Decision"
)

reviewer_note = st.text_area(
    "Reviewer note",
    placeholder=(
        "Optional: explain why this proposal "
        "was approved or rejected."
    ),
)


approve_col, reject_col = st.columns(
    [1, 1]
)


with approve_col:

    approve = st.button(
        "✅ APPROVE",
        use_container_width=True,
        type="primary",
    )


with reject_col:

    reject = st.button(
        "❌ REJECT",
        use_container_width=True,
    )


# ============================================================
# PROPOSAL ID
# ============================================================

proposal_id = make_proposal_id(
    item
)


# ============================================================
# APPROVE
# ============================================================

if approve:

    try:

        client = CRMClient()


        # ====================================================
        # CREATE NEW CRM ACCOUNT
        # ====================================================

        if classification == "NO_CRM_ACCOUNT":

            if not proposed_create:

                st.error(
                    "No account data is available "
                    "for creation."
                )

                st.stop()


            response = client.create_account(
                proposed_create
            )

            new_account_id = response.get(
                "account_id",
                "",
            )


            save_decision(
                proposal_id=proposal_id,
                website_name=website.get(
                    "name",
                    "",
                ),
                crm_account_id=(
                    new_account_id
                ),
                original_classification=(
                    classification
                ),
                decision="APPROVED",
                reviewer_note=reviewer_note,
                approved_changes=json.dumps(
                    {
                        "action": "CREATE",
                        "account": (
                            proposed_create
                        ),
                        "created_account_id": (
                            new_account_id
                        ),
                    },
                    ensure_ascii=False,
                ),
            )


            st.success(
                "Approved. New CRM account "
                "created successfully."
            )


        # ====================================================
        # UPDATE EXISTING CRM ACCOUNT
        # ====================================================

        elif crm_account_id:

            if proposed_changes:

                response = client.update_account(
                    crm_account_id,
                    proposed_changes,
                )

                save_decision(
                    proposal_id=proposal_id,
                    website_name=website.get(
                        "name",
                        "",
                    ),
                    crm_account_id=(
                        crm_account_id
                    ),
                    original_classification=(
                        classification
                    ),
                    decision="APPROVED",
                    reviewer_note=reviewer_note,
                    approved_changes=json.dumps(
                        proposed_changes,
                        ensure_ascii=False,
                    ),
                )


                st.success(
                    "Approved. CRM account "
                    "updated successfully."
                )

                st.json(
                    response
                )

            else:

                save_decision(
                    proposal_id=proposal_id,
                    website_name=website.get(
                        "name",
                        "",
                    ),
                    crm_account_id=(
                        crm_account_id
                    ),
                    original_classification=(
                        classification
                    ),
                    decision="APPROVED",
                    reviewer_note=reviewer_note,
                    approved_changes="{}",
                )


                st.success(
                    "Approved. No CRM update "
                    "was required."
                )


        # ====================================================
        # NO AUTOMATED WRITE
        # ====================================================

        else:

            save_decision(
                proposal_id=proposal_id,
                website_name=website.get(
                    "name",
                    "",
                ),
                crm_account_id="",
                original_classification=(
                    classification
                ),
                decision="APPROVED",
                reviewer_note=reviewer_note,
                approved_changes="{}",
            )


            st.info(
                "Decision recorded. "
                "No automated CRM write was performed."
            )


        st.rerun()


    except Exception as error:

        st.error(
            f"CRM operation failed: {error}"
        )


# ============================================================
# REJECT
# ============================================================

if reject:

    save_decision(
        proposal_id=proposal_id,
        website_name=website.get(
            "name",
            "",
        ),
        crm_account_id=(
            crm_account_id
        ),
        original_classification=(
            classification
        ),
        decision="REJECTED",
        reviewer_note=reviewer_note,
        approved_changes="",
    )


    st.warning(
        "Proposal rejected. "
        "No CRM changes were made."
    )

    st.rerun()