import polars as pl
import requests
from bs4 import BeautifulSoup, Tag
import re
import json
from pathlib import Path
from typing import Dict
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure requests with retries
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5)
session.mount("https://", HTTPAdapter(max_retries=retries))

# Read breed names from CSV
df = pl.read_csv("raw-data/breed_traits.csv")
breed_names = df["Breed"].to_list()

# Get wikipedia page
url = "https://en.wikipedia.org/wiki/List_of_dog_breeds"
response = session.get(url)
soup = BeautifulSoup(response.text, "html.parser")


def normalize_breed_name(name: str) -> str:
    """Normalize breed name for comparison."""
    name = name.lower()
    paren_match = re.search(r"\((.*?)\)", name)
    if paren_match:
        paren_content = paren_match.group(1)
        if "retriever" in name or "spaniel" in name:
            name = f"{paren_content} {name.split('(')[0]}"
    name = re.sub(r"^(dogs|spaniels|retrievers|terriers)\s*", "", name)
    name = re.sub(r"(s|es)$", "", name)
    name = re.sub(r"[^a-z0-9\s]", "", name)
    return name.strip()


def get_breed_variations(name: str) -> list[str]:
    """Generate variations of breed names."""
    variations = {name}
    norm_name = normalize_breed_name(name)
    variations.add(norm_name)

    if "retriever" in name.lower():
        parts = norm_name.split()
        if len(parts) >= 2:
            variations.add(f"{parts[0]} retriever")
            variations.add(f"retriever {parts[0]}")

    if "spaniel" in name.lower():
        parts = norm_name.split()
        if len(parts) >= 2:
            variations.add(f"{parts[0]} spaniel")
            variations.add(f"spaniel {parts[0]}")

    return list(variations)


def extract_breed_from_url(url: str) -> str:
    """Extract breed name from Wikipedia URL."""
    breed = url.split("/")[-1]
    breed = re.sub(r"_dog$", "", breed)
    return breed.replace("_", " ")


def get_breed_page_content(url: str) -> str:
    """Fetch raw HTML content from Wikipedia page."""
    try:
        response = session.get(url)
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching content for {url}: {e}")
        return ""


def is_good_match(breed1: str, breed2: str) -> bool:
    """Determine if two breed names are a good match."""
    words1 = set(breed1.split())
    words2 = set(breed2.split())

    if words1.issubset(words2) or words2.issubset(words1):
        common_words = words1.intersection(words2)
        return (
            len(common_words) >= 2
            or len(common_words) / max(len(words1), len(words2)) >= 0.8
        )
    return False


print("Collecting breed names and URLs...")

# First pass: collect all possible breed names and URLs
breed_variations: Dict[str, str] = {}
for link in soup.find_all("a"):
    href = link.get("href", "")
    if (
        href.startswith("/wiki/")
        and ":" not in href
        and "Main_Page" not in href
        and "List_of" not in href
    ):
        wiki_url = f"https://en.wikipedia.org{href}"
        link_text = link.text.strip()
        url_breed = extract_breed_from_url(href)

        if link_text:
            for variation in get_breed_variations(link_text):
                if len(variation) > 2:
                    breed_variations[variation] = wiki_url
        if url_breed:
            for variation in get_breed_variations(url_breed):
                if len(variation) > 2:
                    breed_variations[variation] = wiki_url

print(f"Found {len(breed_variations)} possible breed variations")

# Second pass: try to match our breed names
print("\nMatching breed names and saving content...")
Path("scripts/tmp").mkdir(exist_ok=True)

breed_matches = []
for breed in breed_names:
    wiki_url = None
    matched_name = None

    # Try all variations of the breed name
    for variation in get_breed_variations(breed):
        if variation in breed_variations:
            wiki_url = breed_variations[variation]
            matched_name = variation
            break

    if not wiki_url:
        norm_breed = normalize_breed_name(breed)
        best_match_score = 0
        for wiki_name, url in breed_variations.items():
            if is_good_match(norm_breed, wiki_name):
                match_score = len(set(norm_breed.split()) & set(wiki_name.split()))
                if match_score > best_match_score:
                    best_match_score = match_score
                    wiki_url = url
                    matched_name = wiki_name

    if wiki_url:
        if matched_name == normalize_breed_name(breed):
            print(f"Found exact match for {breed}")
        else:
            print(f"Found match for {breed} -> {matched_name}")

        # Save raw HTML content
        content = get_breed_page_content(wiki_url)
        if content:
            # Replace non-breaking spaces with regular spaces and remove other problematic characters
            safe_filename = breed.lower().replace("\u00a0", " ").replace(" ", "_")
            safe_filename = re.sub(r"[^a-z0-9_-]", "", safe_filename)
            filename = f"scripts/tmp/wiki_{safe_filename}.html"

            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)

            breed_matches.append(
                {"breed": breed, "wikipedia_url": wiki_url, "content_file": filename}
            )

            time.sleep(1)  # One second delay between requests
    else:
        print(f"No match found for {breed}")
        breed_matches.append({"breed": breed, "wikipedia_url": "", "content_file": ""})

# Save breed matches data
with open("scripts/tmp/breed_matches.json", "w", encoding="utf-8") as f:
    json.dump(breed_matches, f, indent=2)

print("\nCompleted scraping Wikipedia pages")
