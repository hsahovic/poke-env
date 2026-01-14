# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# New target for copying notebooks
copynotebooks:
	cp ../examples/quickstart.ipynb $(SOURCEDIR)/examples
	cp ../examples/using_a_custom_teambuilder.ipynb $(SOURCEDIR)/examples

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile copynotebooks

# Modified catch-all target: now depends on copynotebooks
%: copynotebooks Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
