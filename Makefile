REVEAL_JS=$(CURDIR)/examples/reveal.js

check:
ifndef OE_USERNAME
	$(error OE_USERNAME IS UNDEFINED)
endif
ifndef OE_PASSWORD
	$(error OE_PASSWORD IS UNDEFINED)
endif

install: clean
	pip install .
	pip install jupyter nbconvert

lint:
	autopep8 --in-place --aggressive --aggressive setup.py
	autopep8 --in-place --aggressive --aggressive -r oesdk

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

# https://nbconvert.readthedocs.io/en/latest/install.html
test: check install
	jupyter nbconvert --to markdown --execute $(CURDIR)/examples/SDK-sample-calls.ipynb

serve-nb: check install
	jupyter lab --notebook-dir $(CURDIR)/examples/

$(REVEAL_JS):
	git clone https://github.com/hakimel/reveal.js.git $(REVEAL_JS)

# --post serve
slides: check install $(REVEAL_JS)
	jupyter nbconvert $(CURDIR)/examples/SDK-sample-calls.ipynb \
		--to slides \
		--reveal-prefix $(REVEAL_JS)
