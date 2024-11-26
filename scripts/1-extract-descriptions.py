import json
import wikipediaapi
import csv
from pathlib import Path
import time

# Initialize Wikipedia API
wiki = wikipediaapi.Wikipedia(
    "dog_breeds_project (me@example.com)", "en"  # User agent  # Language
)


def get_page_description(page) -> str:
    """Extract the first meaningful paragraph from a Wikipedia page."""
    if not page.exists():
        return ""

    # Get the full text content
    content = page.text

    # Split into paragraphs and find first meaningful one
    paragraphs = content.split("\n")
    for p in paragraphs:
        p = p.strip()
        # Skip short paragraphs and those that are likely references
        if len(p) > 50 and not p.startswith(("==", "^", "[")):
            return p

    return ""


print("Loading breed matches data...")
with open("scripts/tmp/breed_matches.json", "r", encoding="utf-8") as f:
    breed_matches = json.load(f)

print("\nFetching Wikipedia descriptions...")
output_data = []
for match in breed_matches:
    breed = match["breed"]
    wiki_url = match["wikipedia_url"]

    if wiki_url:
        # Extract page title from URL
        page_title = wiki_url.split("/wiki/")[-1]
        page = wiki.page(page_title)

        description = get_page_description(page)
        if description:
            print(f"Found description for {breed}")
        else:
            print(f"No suitable description found for {breed}")
    else:
        description = ""
        print(f"No Wikipedia URL for {breed}")

    output_data.append(
        {"breed": breed, "wikipedia_url": wiki_url, "description": description}
    )

    # Be nice to Wikipedia's servers
    time.sleep(1)

# Save descriptions to temporary JSON for script 2 to use
print("\nSaving descriptions to JSON...")
Path("scripts/tmp").mkdir(exist_ok=True)
with open("scripts/tmp/breed_descriptions.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2)

print("Completed extracting descriptions")
