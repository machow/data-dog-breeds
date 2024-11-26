import json
import requests
from pathlib import Path
import csv
import time

# Define headers for all requests
HEADERS = {"User-Agent": "dog_breeds_project (me@example.com)"}


def get_page_image(title: str) -> tuple[str, str]:
    """Fetch thumbnail URL and original image URL for a Wikipedia page."""

    # Construct API URL
    api_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "pageimages|pageterms",
        "titles": title,
        "piprop": "thumbnail|original",  # Request both thumbnail and original
        "pithumbsize": "300",  # Request specific thumbnail size
    }

    try:
        response = requests.get(api_url, params=params, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        # Extract image URLs from response
        pages = data.get("query", {}).get("pages", [])
        if pages and "thumbnail" in pages[0]:
            thumb_url = pages[0]["thumbnail"]["source"]
            orig_url = pages[0].get("original", {}).get("source", thumb_url)
            return thumb_url, orig_url
    except Exception as e:
        print(f"Error fetching image for {title}: {e}")

    return "", ""


def download_image(url: str, filepath: Path) -> bool:
    """Download image from URL and save to filepath."""
    if not url:
        return False

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        filepath.write_bytes(response.content)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False


# Create output directory
thumbnails_dir = Path("raw-data/thumbnails")
thumbnails_dir.mkdir(parents=True, exist_ok=True)

# Load descriptions from script 1
print("Loading breed descriptions...")
with open("scripts/tmp/breed_descriptions.json", "r", encoding="utf-8") as f:
    breed_data = json.load(f)

print("\nFetching breed thumbnails...")
for entry in breed_data:
    breed = entry["breed"]
    wiki_url = entry["wikipedia_url"]

    if wiki_url:
        # Extract page title from URL
        page_title = wiki_url.split("/wiki/")[-1]

        # Get image URLs
        thumb_url, orig_url = get_page_image(page_title)

        if thumb_url:
            # Create safe filename from breed name
            safe_breed = breed.lower().replace(" ", "_").replace("\u00a0", " ")
            image_path = thumbnails_dir / f"{safe_breed}.jpg"

            # Download thumbnail
            if download_image(thumb_url, image_path):
                print(f"Downloaded thumbnail for {breed}")
                entry["thumbnail_path"] = str(image_path.name)
            else:
                print(f"Failed to download thumbnail for {breed}")
                entry["thumbnail_path"] = ""
        else:
            print(f"No thumbnail found for {breed}")
            entry["thumbnail_path"] = ""
    else:
        print(f"No Wikipedia URL for {breed}")
        entry["thumbnail_path"] = ""

    # Be nice to Wikipedia's servers
    time.sleep(1)

# Save metadata
print("\nSaving thumbnail metadata...")
metadata_path = thumbnails_dir / "metadata.json"
with open(metadata_path, "w", encoding="utf-8") as f:
    json.dump(breed_data, f, indent=2)

# Write final CSV with descriptions and thumbnail paths
print("\nSaving breed descriptions and thumbnails to CSV...")
Path("raw-data").mkdir(exist_ok=True)
with open(
    "raw-data/wiki_breed_descriptions.csv", "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=["breed", "wikipedia_url", "description", "thumbnail_path"]
    )
    writer.writeheader()
    writer.writerows(breed_data)

print("Completed extracting thumbnails and creating final CSV.")
