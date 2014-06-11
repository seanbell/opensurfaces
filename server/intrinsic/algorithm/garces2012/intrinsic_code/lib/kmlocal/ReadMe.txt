------------------------------------------------------------------------
KMlocal: A testbed for k-means clustering algorithms based on local
search
Version: 1.7.3
Date: 01/27/2010
------------------------------------------------------------------------
Copyright (c) 2004-2010 David M. Mount and the University of Maryland
All Rights Reserved.

PLEASE READ THE FILE "Copyright.txt" FOR COPYRIGHT INFORMATION AND
DISCLAIMER.

Author
------
David Mount
Dept of Computer Science
University of Maryland,
College Park, MD 20742 USA
mount@cs.umd.edu
http://www.cs.umd.edu/~mount/
------------------------------------------------------------------------

For detailed explanation of the k-means algorithm and technical
information the use of the program see the documentation file
doc/kmlocal-doc.pdf.

Organization
------------
The source files for the testbed are stored mostly in src.  The
directory ann contains utilities for building and search kd-trees.
Consult the file README files in those directories for further
information.

The main executable file is kmltest.  It is a driver, which provides a
primitive script language for inputting and generating data sets,
running different algorithms on these data sets, and printing
statistical results.  There is a utility km2fig, which produces xfig
output from the kmltest output files.  This is handy for generating
figures for papers.

	README		This file.
	Makefile	The Makefile for compiling/testing everything.
	bin/		Where the executables are stored (kmltest)
	src/		The directory containing all the source files.
	test/		Some test input/output files for validation.

Compilation
-----------
To start, you can compile kmltest (in theory) by entering (from this
directory) "make".  This is set up for the g++ compiler (version 2.7.2
or higher) on Solaris and will probably generate a number of error
messages if you try it from another compiler or platform.  (I made no
attempt to make it ANSI compatible).

The program kmltest is the main driver for the algorithms.  See the file
src/kmltest-README for more information on the input to kmltest.  To get
a sense of what input files look like, you can look at the *.in files in
directory test.  (By the way, don't trust any of the comments in these
files.)

Validation
----------
To validate that you have successfully compiled everything enter (from
this directory) "make validate".  This will compare the results of my
runs with the currently compiled version.  Assuming the same
architecture (Sun Solaris), and same random number generator (random())
you should expect the same numerical results, although execution times
will differ.

If the random number generator is different then results will differ
massively, since the algorithm's output is very sensitive to the initial
set of centers, which are chosen randomly.

Final Warning
-------------
Don't believe anything you read. (Not even this file). The program does
what it does; nothing more, nothing less.  :-)

History
-------
Version: 1.0	04/29/2002	Initial release
Version: 1.01	10/02/2002	Modified output levels
Version: 1.1	04/08/2003	Added EZ_Hybrid and dampening.  Fixed
				memory leaks.
Version: 1.2	09/13/2003	No changes to the program.  Created
				documention directory.  Added sample
				programs, kmlsample.cpp and kmlminimal.cpp.
Version: 1.3	01/18/2004	No changes to the program.  Converted
				license to GNU General Public License
Version: 1.4	02/05/2004	No changes to the program.  Added a test
				for kmlminimal and kmlsample in the test
				directory.
Version: 1.5	05/14/2004	Changed sample program kmlsample to
				allow random point generation.  Made
				minor changes for compilation under
				Redhat Linux and Visual Studio.NET.
Version: 1.6	03/09/2005	Fixed memory leak in KMfilterCenters.cpp,
				added project file for Microsoft Studio.NET,
				and fixed random number error for Microsoft
				Visual C++.
Version: 1.7	08/10/2005	Fixed errors in documentation.  Added
				capability for reporting final assignment
				to clusters.
Version: 1.7.1	10/01/2005	No functional change. Corrected copyright
				text in source files.
Version: 1.7.2	01/27/2010	Minor updates for modern compilers.
