.PHONY: build serve test

build:
	bundle exec jekyll build --destination _site

serve:
	bundle exec jekyll serve

test:
	@tmp=$$(mktemp -d); trap 'rm -rf "$$tmp"' EXIT; \
	  bundle exec jekyll build --destination "$$tmp" && \
	  JEKYLL_DESTINATION="$$tmp" python3 -m unittest discover -s tests -v
