---------------------------------------------------------------------
Intrinsic Images by Clustering
Version: 1.0
Date: 20/07/2012
---------------------------------------------------------------------
Copyright (C) 2012 Elena Garces and Adolfo Muñoz
All Rights Reserved.

PLEASE READ THE FILE "Copyright.txt" FOR COPYRIGHT INFORMATION AND
DISCLAIMER.

---------------------------------------------------------------------
Authors
---------------------------------------------------------------------
Elena Garces
Universidad de Zaragoza
Departamento de Informática e Ingeniería de Sistemas
EINA (Edificio Ada Byron)
C/ María de Luna, 1
50018, Zaragoza
ESPAÑA.
egarces@unizar.es

Adolfo Muñoz
Universidad de Zaragoza
Departamento de Informática e Ingeniería de Sistemas
EINA (Edificio Ada Byron)
C/ María de Luna, 1
50018, Zaragoza
ESPAÑA
adolfo@unizar.es
www.adolfo-munoz.com


---------------------------------------------------------------------
PAPER
---------------------------------------------------------------------
This program implements the following paper (please use it for reference):

@article{Garces2012,
    author = {Garces, Elena and Munoz, Adolfo and Lopez-Moreno, Jorge and Gutierrez, Diego},
    title = {Intrinsic Images by Clustering},
    journal = {Computer Graphics Forum (Proc. EGSR 2012)},
    year = {2012},
    volume = {31},
    number = {4},
}

Project Webpage: http://giga.cps.unizar.es/~elenag/projects/EGSR2012_intrinsic/

This software package is provided for research purposes only. We hope it will be useful!

---------------------------------------------------------------------
MAIN FILES AND FOLDERS INCLUDED:
---------------------------------------------------------------------
	README 				This file

	/intrinsic_code		Our code
		/intrinsic_code/include
		/intrinsic_code/src


	/lib				External Dependencies
		/lib/CImg		CImg library (http://cimg.sourceforge.net/)
		/lib/IML++  		QMR implementation (http://math.nist.gov/iml++/)
		/lib/kmlocal		KMEANS implementation
						(KMlocal: A testbed for k-means clustering algorithms based on local search
						Copyright (c) 2004-2010 David M. Mount and the University of Maryland)

	/results			Directory where the results are saved
	/examples


IMPORTANT:
** This program requires the BOOST LIBRARY which is not provided. You can download it here: http://www.boost.org/users/download/
** The package is prepared to compile and execute with MS Visual Studio 2010 although all c++ files will be able to run over unix systems.

---------------------------------------------------------------------
USAGE
---------------------------------------------------------------------

You have two options to run our code.

FIRST OPTION. Run KMEANS segmentation using  KMlocal implementation by David M. Mount.
For this option you only have to set up the initial number of clusters (by default is 10)

SECOND OPTION. Introduce your own segmentation file. Format of the file:
- It must be a plain .pgm file
- It must contain the segmentation in the form of a matrix of labels (similar to MATLAB labels)
- The labels must be integer numbers starting by 1. No additional data or compression is required for the file.
- There are some examples in .\examples\*\ directories with the name: *_segmentationKmeans.pgm


intrinsic_code.exe -i input [-m mask] [-no-useRcte] [-only-seg] [-no-gamma] [SEGMENTATION OPTIONS]

-i input          input image
-m mask           optional: mask file
-no-useRcte	  optional: not include reflectance similarity equations (default off)
-only-seg         optional: run only the clustering stage (default off)
-no-gamma         optional: flag to not apply gamma correction (2.2) to the input image (default off)

	SEGMENTATION OPTIONS
		-segMode mode     segmentation mode=[KMEANS opt | FILE file] (default KMEANS)

		                    *if [KMEANS opt], additional options are [-km-k k] where k
		                     is the number of clusters (default k=10)
								e.g. -segMode KMEANS -km-k 5

							 *if [FILE file], a segmentation file must be provided
								e.g. -segMode FILE D:\Images\sun_segmentation.pgm


		-th-lum-max th_max (default 95)
		-th-lum-min th_min (default 15)
		-th-cr-min th_croma (default 20)
			These three parameters control the black and white detection thresholds (see section 3.1 for details) (defined by percentages)

		-porc_grad percentage (default 0.01)
			This parameter controls the degree of merging (see secion 3.1 Merging Smooth Boundaries for details)


---------------------------------------------------------------------
HOW TO USE THE EXAMPLES
---------------------------------------------------------------------

The same shading and reflectance images will be obtained from the following two options:

1. Segmentation with kmeans. Ouput directory: .\results\Kmeans\
	intrinsic_code.exe -i .\examples\moscow\moscow.png -seg-mode KMEANS -km-k 10

	This operation will generate 4 files:
	* moscow_k10_reflectance.ppm
	* moscow_k10_shading.ppm
	* moscow_k10_segmentationKmeans.bmp
	* moscow_k10_segmentationKmeans.pgm

	The last 2 files are the results of KMEANS.
	*.pgm file contains the labels
	*.bmp file is the segmentation painted for visualization purposes only


2. Segmentation from File. Ouput directory: .\results\File\
	Once you have computed the segmentation and you are happy with it, there is no need to do it always.
	Hence, you can load the precomputed segmentation file *.pgm

	intrinsic_code.exe -i .\examples\moscow\moscow.png -seg-mode FILE .\examples\moscow\moscow_k10_segmentationKmeans.pgm



