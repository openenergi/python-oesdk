REVEAL_JS=$(CURDIR)/examples/reveal.js

check:
ifndef OE_USERNAME
	$(error OE_USERNAME IS UNDEFINED)
endif
ifndef OE_PASSWORD
	$(error OE_PASSWORD IS UNDEFINED)
endif

install: clean
	pip install --upgrade pip
	pip install --editable . -vv
	pip install jupyter nbconvert

format:
	black oesdk

lint-errors:
	flake8 --ignore=E501,W503,W504, oesdk tests*
	pytype --keep-going --jobs 6 oesdk
	pylint --disable=R,C,W,E1101,I1101 oesdk

clean:
	-find . \
		-name __pycache__ \
		-type d  \
		-exec rm -rf {} \;
	-rm -r \
		examples/.ipynb_checkpoints \
		examples/*html \
		examples/*pdf \
		examples/*md
	-pip uninstall -y oesdk

nb-markdown:
	jupyter nbconvert --to markdown --execute $(CURDIR)/examples/SDK-sample-calls.ipynb

test: check
	python -m unittest discover -s tests -v

serve-nb: check install
	jupyter lab --notebook-dir $(CURDIR)/examples/

$(REVEAL_JS):
	git clone https://github.com/hakimel/reveal.js.git $(REVEAL_JS)

# --post serve
slides: check install $(REVEAL_JS)
	jupyter nbconvert $(CURDIR)/examples/SDK-sample-calls.ipynb \
		--to slides \
		--reveal-prefix $(REVEAL_JS)
