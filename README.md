# Dog breeds data

This repository contains data on how dog breeds score on different traits. It's used to create a beautiful demo table for reactable-py.

## Data

The basic trait data comes from tidytuesday:

- **raw-data/breed_traits.csv**: each row is a dog breed, and each trait is a column.
  - The Breed column contains the name of the breed.
  - Example traits are Affectionate with Family, Shedding level, etc..
- **raw-data/breed_rank.csv**: relative popularity of each breed over several years.
- **raw-data/trait_description**.csv: alternative names for each trait, and a description.

Breed images and descriptions can be found on wikipedia (https://en.wikipedia.org/wiki/List_of_dog_breeds), and will be as follows:

- **raw-data/wiki_breed_images.csv**: each row is a dog breed, and each column is a link to an image of the breed.
- **raw-data/wiki\_{breed_name}.png**: image of the breed.
- **raw-data/wiki_breed_descriptions.csv**: each row is a dog breed, along with its wikipedia url and description.

## Generating data

(WIP) run scripts/0-scrape-wikipedia.py to populate breed images and descriptions.
