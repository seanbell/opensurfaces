#-----------------------------------------------------------------------------
# Makefile for the kMeans test and evaluation program
#
# Adjust parameters below for various directories and compiler choices.
# Then do:
#
#	make				compiles kmltest
#	make all			compiles kmltest, kmlsample, kmlminimal
#	make test			compiles kmltest
#	make sample			compiles kmlsample
#	make minimal			compiles kmlsample
#
# The executables are stored in ../bin
#
# Other targets:
#
#	make clean			delete temporary files
#	make realclean			delete temp and executables
#	make print			print everything
#
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Basic definitions
#		BIN_DIR		where to store executables
#		LDFLAGS		loader flags
#		OTHERLIBS	other library flags
#-----------------------------------------------------------------------------

BIN_DIR		= ../bin
OTHERLIBS	= -lm

#-----------------------------------------------------------------------------
# Some more definitions
#		KMLTEST		path to the test executable
#		KMLSAMPLE	path to the sample executable
#		KMLMINIMAL	path to the minimal sample
#-----------------------------------------------------------------------------

KMLTEST = $(BIN_DIR)/kmltest
KMLSAMPLE = $(BIN_DIR)/kmlsample
KMLMINIMAL = $(BIN_DIR)/kmlminimal

TESTSOURCES = KM_ANN.cpp KMeans.cpp  KMterm.cpp KMrand.cpp \
	KCutil.cpp KCtree.cpp KMdata.cpp KMcenters.cpp \
	KMfilterCenters.cpp KMlocal.cpp

TESTOBJECTS = $(TESTSOURCES:.cpp=.o)

#-----------------------------------------------------------------------------
# Compiler and compilation options:
#
#	C++		your C++ compiler
#	CFLAGS (for g++)
#		-O[1-3]        	Optimization
#		-Wall		Be noisy about warnings
#		-traditional	Flag nontraditional C++ usage
#		-g          	Debugging
#                               (may slow execution slightly)
#		-DASSERT	Enable assertion checking
#                               (may slow execution slightly)
#	WAIT_FOR_COMFIRM	Force user to confirm program termination
#				(Useful in some PC versions, which create a
#				temporary command terminal in which to run
#				the program.)
#-----------------------------------------------------------------------------
C++ = g++
#CFLAGS = -O3 
#CFLAGS = -g -Wall -DASSERT -traditional
CFLAGS = -O3 -Wall -DASSERT

#-----------------------------------------------------------------------------
# Make the program
#-----------------------------------------------------------------------------

default: $(KMLTEST)

all: $(KMLTEST) $(KMLSAMPLE) $(KMLMINIMAL)

test: $(KMLTEST) 

sample: $(KMLSAMPLE) 

minimal: $(KMLMINIMAL) 

$(KMLTEST): $(TESTOBJECTS) kmltest.o
	$(C++) $(TESTOBJECTS) kmltest.o -o kmltest $(LDFLAGS) $(OTHERLIBS)
	mv -f kmltest $(KMLTEST)

$(KMLSAMPLE): $(TESTOBJECTS) kmlsample.o
	$(C++) $(TESTOBJECTS) kmlsample.o -o kmlsample $(LDFLAGS) $(OTHERLIBS)
	mv -f kmlsample $(KMLSAMPLE)

$(KMLMINIMAL): $(TESTOBJECTS) kmlminimal.o
	$(C++) $(TESTOBJECTS) kmlminimal.o -o kmlminimal $(LDFLAGS) $(OTHERLIBS)
	mv -f kmlminimal $(KMLMINIMAL)

#-----------------------------------------------------------------------------
# Object files
#-----------------------------------------------------------------------------

KM_ANN.o: KM_ANN.h KM_ANN.cpp
	$(C++) -c $(CFLAGS) KM_ANN.cpp

KMeans.o: KM_ANN.h KMeans.h KMeans.cpp
	$(C++) -c $(CFLAGS) KMeans.cpp

KMterm.o: KMterm.h KMterm.cpp
	$(C++) -c $(CFLAGS) KMterm.cpp

KMrand.o: KMeans.h KMrand.h KMrand.cpp
	$(C++) -c $(CFLAGS) KMrand.cpp

KCutil.o: KMeans.h KCutil.h KCutil.cpp
	$(C++) -c $(CFLAGS) KCutil.cpp

KCtree.o: KM_ANN.h KMeans.h KCutil.h KCtree.h KCtree.cpp
	$(C++) -c $(CFLAGS) KCtree.cpp

KMdata.o: KMeans.h KMdata.h KMdata.cpp
	$(C++) -c $(CFLAGS) KMdata.cpp

KMcenters.o: KMeans.h KMdata.h KMcenters.h KMcenters.cpp
	$(C++) -c $(CFLAGS) KMcenters.cpp

KMfilterCenters.o: KMeans.h KMdata.h KMcenters.h KMfilterCenters.h \
	KMfilterCenters.cpp
	$(C++) -c $(CFLAGS) KMfilterCenters.cpp

KMlocal.o: KMeans.h KMdata.h KMcenters.h KMfilterCenters.h \
	KMlocal.h KMlocal.cpp
	$(C++) -c $(CFLAGS) KMlocal.cpp

#-----------------------------------------------------------------------------
# Test and Sample Program
#-----------------------------------------------------------------------------

kmltest.o: KMeans.h KMdata.h KMcenters.h KMfilterCenters.h \
	KMlocal.h KMterm.h kmltest.cpp
	$(C++) -c $(CFLAGS) kmltest.cpp

kmlsample.o: KMeans.h KMdata.h KMcenters.h KMfilterCenters.h \
	KMlocal.h KMterm.h kmlsample.cpp
	$(C++) -c $(CFLAGS) kmlsample.cpp

kmlminimal.o: KMeans.h KMdata.h KMcenters.h KMfilterCenters.h \
	KMlocal.h KMterm.h kmlminimal.cpp
	$(C++) -c $(CFLAGS) kmlminimal.cpp

#-----------------------------------------------------------------------------
# Miscellaneous
#-----------------------------------------------------------------------------

PRINT_QUEUE = ps3

print:
	enscript -2r -G -P $(PRINT_QUEUE) \
		KM_ANN.h KM_ANN.cpp \
		KMeans.h KMeans.cpp \
		KCutil.h KCutil.cpp \
		KCtree.h KCtree.cpp \
		KMdata.h KMdata.cpp \
		KMcenters.h KMcenters.cpp \
		KMfilterCenters.h KMfilterCenters.cpp \
		KMlocal.h KMlocal.cpp \
		KMterm.h KMterm.cpp \
		kmltest.cpp \
		kmlsample.cpp \
		kmlminimal.cpp

#-----------------------------------------------------------------------------
# Cleaning
#-----------------------------------------------------------------------------

clean:
	-rm -f *.o *.obj *.fig *.bak *.dmp *.~cpp *.~h core

realclean: clean
	-rm -f $(KMLTEST) $(KMLSAMPLE) $(KMLMINIMAL)
