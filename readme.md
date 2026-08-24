# Bellhaven CRM Reconciliation

A small reconciliation pipeline that compares Bellhaven website locations with CRM accounts, identifies discrepancies, and provides a human-reviewed workflow for updating the CRM.

## What It Does

The pipeline:

1. Scrapes all Bellhaven locations from the website.
2. Retrieves CRM accounts through the provided API.
3. Matches website locations to CRM accounts using normalized names, addresses, city, state, ZIP code, and phone numbers.
4. Classifies the results and creates a review queue.
5. Provides supporting evidence for each proposed change.
6. Requires explicit reviewer approval before writing changes to the CRM.
7. Runs daily through GitHub Actions.

## Matching Categories

- `CONFIDENT_MATCH` - strong evidence that the website location matches the CRM account.
- `NEEDS_FIX` - likely match but requires a CRM correction.
- `NO_CRM_ACCOUNT` - website location has no suitable CRM account.
- `DUPLICATE` - CRM account appears to be a duplicate.
- `CRM_NOT_ON_WEBSITE` - CRM account has no corresponding current website location.

## Review Workflow

The review application shows:

- Classification
- Match score
- CRM account
- Matching evidence
- CRM data
- Proposed CRM change

A reviewer can **Approve** or **Reject** each proposal.

CRM changes are never made automatically.

Approved changes are written through the CRM API. Review decisions are stored locally so previously decided proposals are not re-proposed on subsequent runs.

## Billing / Parent Account Rule

When an account needs to move to a different parent, the pipeline checks `lifetime_revenue` and `outstanding_ar`.

If an account has both revenue history and outstanding AR, the existing account is preserved. A new account is created under the correct parent and the old account is linked to it through `chow_current_account`.

Otherwise, the existing account can be re-parented directly.

For duplicates, the losing account is marked `Inactive` and linked to the surviving account through `duplicate_of_account`. The API does not support merge or delete operations.

## Project Structure

```text
.
├── app.py
├── requirements.txt
├── data/
│   ├── raw/
│   └── processed/
├── src/
│   ├── scraper.py
│   ├── api.py
│   ├── matcher.py
│   ├── classifier.py
│   ├── review.py
│   ├── review_db.py
│   └── daily_pipeline.py
└── .github/
    └── workflows/
        └── daily_pipeline.yml