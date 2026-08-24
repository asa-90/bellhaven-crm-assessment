import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def run_step(
    description,
    script_name,
):

    print()
    print("=" * 70)
    print(description)
    print("=" * 70)

    script_path = (
        BASE_DIR
        / "src"
        / script_name
    )

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
        ],
        cwd=BASE_DIR,
    )

    if result.returncode != 0:

        raise RuntimeError(
            f"Pipeline step failed: "
            f"{description}"
        )


def main():

    print("=" * 70)
    print("BELLHAVEN DAILY PIPELINE")
    print("=" * 70)


    # ========================================================
    # STEP 1
    # ========================================================

    run_step(
        "STEP 1 - SCRAPE BELLHAVEN WEBSITE",
        "scraper.py",
    )


    # ========================================================
    # STEP 2
    # ========================================================

    run_step(
        "STEP 2 - FETCH CRM ACCOUNTS",
        "api.py",
    )


    # ========================================================
    # STEP 3
    # ========================================================

    run_step(
        "STEP 3 - RUN MATCHING",
        "matcher.py",
    )


    print()
    print("=" * 70)
    print("DAILY PIPELINE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":

    main()