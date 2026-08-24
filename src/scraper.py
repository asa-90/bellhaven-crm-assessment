import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


BASE_URL = "https://analyst-assessment-production.up.railway.app"
COMMUNITIES_URL = f"{BASE_URL}/communities"


def get_community_urls():
    community_urls = []
    current_url = COMMUNITIES_URL

    while current_url:
        print(f"Scraping directory: {current_url}")

        response = requests.get(
            current_url,
            timeout=30,
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Find community detail links
        for link in soup.find_all("a", href=True):
            href = link["href"]

            if href.startswith("/communities/"):
                full_url = urljoin(BASE_URL, href)

                if full_url not in community_urls:
                    community_urls.append(full_url)

        # Find the next page
        next_url = None

        for link in soup.find_all("a", href=True):
            text = link.get_text(" ", strip=True)

            if text.lower().startswith("next"):
                next_url = urljoin(BASE_URL, link["href"])
                break

        current_url = next_url

    return community_urls


    response = requests.get(
        url,
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for element in soup.find_all(string=lambda text: text and "210 Orchard Lane" in text):
        print("\nADDRESS ELEMENT:")
        print(element.parent)

    name = soup.find("h1").get_text(" ", strip=True)

    page_text = soup.get_text(" ", strip=True)

    print(f"Scraping: {name}")

    return {
        "name": name,
        "page_text": page_text,
        "url": url,
    }

def scrape_community(url):
    response = requests.get(
        url,
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Facility name
    name_element = soup.find("h1")
    name = name_element.get_text(" ", strip=True)

    # Helper function to get the value belonging to a <dt> label
    def get_definition_value(label):
        dt = soup.find(
            "dt",
            string=lambda text: (
                text and text.strip().lower() == label.lower()
            ),
        )

        if not dt:
            return ""

        dd = dt.find_next_sibling("dd")

        if not dd:
            return ""

        return dd.get_text(" ", strip=True)

    # Address
    address_element = soup.find(
        "dt",
        string=lambda text: (
            text and text.strip().lower() == "address"
        ),
    )

    address = ""
    city = ""
    state = ""
    zip_code = ""

    if address_element:
        address_dd = address_element.find_next_sibling("dd")

        if address_dd:
            address_parts = list(
                address_dd.stripped_strings
            )

            if len(address_parts) >= 2:
                address = address_parts[0]

                location = address_parts[1]

                location_parts = location.rsplit(" ", 2)

                if len(location_parts) == 3:
                    city = location_parts[0].rstrip(",")
                    state = location_parts[1]
                    zip_code = location_parts[2]

    # Other fields
    care_offerings_text = get_definition_value(
        "Care Offerings"
    )

    administrator = get_definition_value(
        "Administrator"
    )

    phone = get_definition_value(
        "Phone"
    )

    # Care offerings
    care_offerings = []

    if care_offerings_text:
        care_offerings = [
            item.strip()
            for item in care_offerings_text.split(",")
            if item.strip()
        ]

    return {
        "name": name,
        "address": address,
        "city": city,
        "state": state,
        "zip": zip_code,
        "care_offerings": care_offerings,
        "administrator": administrator,
        "phone": phone,
        "source_url": url,
    }

if __name__ == "__main__":
    community_urls = get_community_urls()

    print(
        f"\nFound {len(community_urls)} community URLs."
    )

    communities = []
    errors = []

    for index, url in enumerate(
        community_urls,
        start=1,
    ):
        print(
            f"[{index}/{len(community_urls)}] "
            f"Scraping {url}"
        )

        try:
            community = scrape_community(url)
            communities.append(community)

        except Exception as error:
            print(
                f"ERROR scraping {url}: {error}"
            )

            errors.append({
                "url": url,
                "error": str(error),
            })

    print(
        f"\nSuccessfully scraped "
        f"{len(communities)} communities."
    )

    print(
        f"Failed: {len(errors)}"
    )

    # Save scraped data
    output_file = "data/raw/bellhaven_locations.json"

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            communities,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"\nSaved scraped data to: {output_file}"
    )     