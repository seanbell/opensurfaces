#-----------------------------------------------------------------------------
# Makefile for KMlocal documentation
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Basic definitions
#		BASEDIR		where include, src, bin, ... are
#		KMDOC		name of documentation
#-----------------------------------------------------------------------------

BASEDIR	= ..
KMDOC   = kmlocal-doc

#-----------------------------------------------------------------------------
# Make the program
#-----------------------------------------------------------------------------

default: ps

ps: $(KMDOC).ps
pdf: $(KMDOC).pdf
dvi: $(KMDOC).dvi

$(KMDOC).pdf: $(KMDOC).ps
	distillx $(KMDOC).ps

$(KMDOC).ps: $(KMDOC).dvi
	dvips -P pdf $(KMDOC).dvi

$(KMDOC).dvi: $(KMDOC).tex
	latex $(KMDOC).tex
	latex $(KMDOC).tex

#-----------------------------------------------------------------------------
# Cleaning
#-----------------------------------------------------------------------------

clean:
	-rm -f core *.aux *.dvi *.log *.blg *.bbl *.toc;

realclean: clean
