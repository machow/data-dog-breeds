scripts/tmp/breed_matches.json: scripts/0-scrape-wiki.py
	python scripts/0-scrape-wiki.py

scripts/tmp/breed_descriptions.json: scripts/1-extract-descriptions.py scripts/tmp/breed_matches.json
	python scripts/1-extract-descriptions.py

raw-data/wiki_breed_descriptions.csv: scripts/2-extract-thumbnails.py scripts/tmp/breed_descriptions.json
	python scripts/2-extract-thumbnails.py

demos/dog-traits/thumbnails: raw-data/thumbnails
	rm -rf $@
	cp -r $< $@

.PHONY: all
all: raw-data/wiki_breed_descriptions.csv
