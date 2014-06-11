//----------------------------------------------------------------------
//	File:			main.cpp
//	Author:			Elena Garces
//	Last modified:	18/07/2012
//	Description:	main program
//----------------------------------------------------------------------
// This file is part of Intrinsic Images by Clustering.
//
//    Intrinsic Images by Clustering is free software: you can redistribute it
//    and/or modify it under the terms of the GNU General Public License as
//    published by the Free Software Foundation, either version 3 of the License,
//     or (at your option) any later version.
//
//    Intrinsic Images by Clustering is distributed in the hope that it will
//    be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//    GNU General Public License for more details.
//
//    You should have received a copy of the GNU General Public License
//    along with Intrinsic Images by Clustering.  If not,
//	  see <http://www.gnu.org/licenses/>.
////----------------------------------------------------------------------

#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <fstream>
#include <string>
#include <time.h>

#define cimg_OS 1
#define cimg_display 0
#define cimg_plugin1 <../lib/CImg/cimg-additions2.h>
#include <CImg.h>

#include "auxiliar.h"
#include "normalizator.h"
#include "matte.h"
#include "segmentacion.h"
#include "kmeans-segmentator.h"



using namespace Imaging;

int main(int argc, char **argv) {

	time_t start,end;
	double diff;

	time(&start);


	/* GET THE ARGUMENTS FROM THE COMMAND LINE */
	gral_params params = getArgs(argc, argv);


	CImg<double> im_input_rgb(params.name_input.c_str());

	/* LOADING MASK FILE */
	Imaging::MatteImage matteImg;
	if (!params.name_mask.empty())
		matteImg = Imaging::MatteImage(params.name_mask.c_str());
	else
	{
		CImg<float> aux(im_input_rgb.width(),im_input_rgb.height(),1,1);
		aux.fill(255.0);
		matteImg = Imaging::MatteImage(aux);
	}


	/* CORRECTING GAMMA (DEFAULT 2.2)*/
	if (params.gammaCorrect)
		{
			im_input_rgb.pow(2.2);
			/* hack*///im_input_rgb/=0.7;
		}

	/* ------------ LAB ------------*/
	CImg<double> imgLab(im_input_rgb);
	imgLab*=255.0/imgLab.max();
	imgLab.RGBtoLab();




	Segmentacion segmentation(im_input_rgb.width(),im_input_rgb.height());
	segmentation.set(argc, argv); /* read params from command line */

	params.name_output.assign(build_name_output(params, segmentation.segMode));

	/* ------------------------------------------------------------ */
	/*           STEP 1. CLUSTERING						            */
	/* ------------------------------------------------------------ */

	switch(segmentation.segMode)
	{
		case FILE_SEG:
			{
			#ifdef VERBOSE
				cout << "Clustering: --> From file.\n" << endl;

			#endif
			/* DO NOTHING (FILE ALREADY LOADED)*/
			break;
			}

		case KMEANS_SEG:

			{
			#ifdef VERBOSE
				cout << "Clustering: --> Running Kmeans.\n" << endl;
			#endif

			double maxLUM=(segmentation.lum_th_max/100.0)*imgLab.get_channel(0).max();
			double minLUM=(segmentation.lum_th_min/100.0)*imgLab.get_channel(0).max();
			double minCROMA = (segmentation.croma_th_min/100.0)*std::max(imgLab.get_channels(1,2).max(),fabs(imgLab.get_channels(1,2).min()));


			Imaging::Segment::KMeansSegmentator kmeanseg;
			kmeanseg.set(argc,argv, params.name_output); /* initialize and read params from command line */
			kmeanseg.segmentate(imgLab.get_channels(1,2), segmentation, matteImg);
			segmentation.updateLabels();

			/* BLACK AND WHITE SEPARATION */
			cimg_forXY(imgLab,x,y)
			{
				if (matteImg(x,y))
				{
					if (fabs(imgLab(x,y,0,1)) < minCROMA && fabs(imgLab(x,y,0,2)) < minCROMA)
					{
						if (imgLab(x,y,0,0) < minLUM)
							segmentation.setCluster(x,y,segmentation.nclusters()+1);
							if (imgLab(x,y,0,0) > maxLUM)
							segmentation.setCluster(x,y,segmentation.nclusters()+2);
					}
				}
			}
			segmentation.updateLabels();

			/* save results */
			string name_aux(params.name_output), name_aux2(params.name_output);
			(segmentation.imageMapLabels+1).save(name_aux.append("_segmentationKmeans.pgm").c_str());

			CImg<double> output_seg(im_input_rgb); segmentation.colorize_coherent(output_seg);
			output_seg.save(name_aux2.append("_segmentationKmeans.bmp").c_str());


			break;
			}


		/*case XXX: you can include your own segmentation algorithm here */
	}

	#ifdef VERBOSE
	cout << "Clustering: --> Step 0. Initial number of Segments " << segmentation.getListOfClusters().size() << endl;
	#endif


	/* Clustering in image space */
	Segmentacion clustering(im_input_rgb.width(),im_input_rgb.height());
	clustering = segmentation.get_separate_noncontiguous_clusters();
	clustering.updateLabels();
	#ifdef VERBOSE
	cout << "Clustering: --> Step 1. After clustering in image space, nclus =  " << clustering.getListOfClusters().size() << endl;
	#endif

	/* search vectors of similar reflectance by comparing the old segmentation with the new clustering */
	vector<tpPair> pairsReflectance;
	if (params.useRsimPairs)
		pairsReflectance = clustering.searchPairsRcte(segmentation);



	/* no dependency problems between searchPairsRcte and both functions: mergeSmallClusters and mergeSmoothBoundaries.
	These functions only remove clusters smaller than 10 pixels. While searchPairsRcte only take pairs
	of clusters bigger than 100 pixels */

	/* Merging small clusters */
	#ifdef VERBOSE
	cout << "Clustering: --> Step 2. Merging small clusters " << endl;
	#endif

	clustering.mergeSmallClusters(imgLab, 10, 10, 0.8);
	int i = 1;
	while (clustering.nclusters() > 5000 && i < 10)
	{
		/* in case we had oversegmentation, it is desirable to reduce the number of clusters to improve efficiency*/
		clustering.mergeSmallClusters(imgLab, 10, 10*i, 0.8);
		i++;
	}

	/* Merging smooth boundaries */
	#ifdef VERBOSE
	cout << "Clustering: --> Step 3. Merging smooth boundaries " << endl;
	#endif

	int it=1;
	int n_changes = clustering.mergeSmoothBoundaries(&im_input_rgb, matteImg, pairsReflectance);

	#ifdef VERBOSE
	cout << "Clustering: --> \t\tIteration " << it <<" changes " << n_changes << endl;
	#endif

	while (n_changes > 0)
	{
		it++;
		n_changes = clustering.mergeSmoothBoundaries(&im_input_rgb, matteImg, pairsReflectance);
		#ifdef VERBOSE
		cout << "Clustering: --> \t\tIteration " << it <<" changes " << n_changes << endl;
		#endif
	}


	#ifdef VERBOSE
		cout << "Clustering: --> FINAL number of clusters " << clustering.nclusters() << endl;
	#endif

	if (params.useRsimPairs)
	{
		#ifdef VERBOSE
		cout << "Clustering: --> FINAL number of pairs with similar reflectance " << pairsReflectance.size() << endl;
		#endif
	}

	time(&end);
	diff = difftime(end,start);

	printf("Clustering: --> Running time %.1f seconds\n", diff);


	/* --------- SAVE PARTIAL RESULTS OF CLUSTERING --------- */
	//clustering.imageMapLabels +=1;
	//string name_aux(params.name_output);
	//CImg<double> output_seg(im_input_rgb); clustering.colorize_coherent(output_seg);
	//output_seg.save(name_aux.append("_clustering.bmp").c_str());
	//clustering.imageMapLabels -=1;

	/* ------------------------------------------------------------ */
	/*   STEP 2. BUILDING AND SOLVING THE SYSTEM OF EQUATIONS       */
	/* ------------------------------------------------------------ */
	if (params.system_definition)
	{
		time(&start);
		#ifdef VERBOSE
		cout << "\nSystem Definition: --> Starts"<< endl;
		#endif

		/* --- > luminance image */
		double luminance_factors[] = {0.2125,0.7154,0.0721};
		CImg<double> img_luminance(im_input_rgb.get_dot_product_C(luminance_factors));

		/* In case we removed clusters in the merging process, we need to check again the consistency of the pairs
		of clusters with similar reflectance */
		clustering.updateReflectancePairs(pairsReflectance, &img_luminance);

		Normalization::Normalizator normalizator(argc,argv);
		normalizator.normalize(clustering, img_luminance, im_input_rgb, matteImg, &pairsReflectance);


		/* ------------------------------------------------------------ */
		/*           STEP 3. PRINT SHADING AND REFLECTANCE            */
		/* ------------------------------------------------------------ */
		char name_dst3[200], name_dst5[200];

		strcpy(name_dst3,params.name_output.c_str()); strcat(name_dst3, "_shading.pgm");
		strcpy(name_dst5,params.name_output.c_str()); strcat(name_dst5, "_reflectance.ppm");

		if (params.gammaCorrect) img_luminance.pow(1/2.2);

		img_luminance*=MAX_RANGE_LUM/img_luminance.max(); /* NORMALIZE */

		CImg<double> reflectance(params.name_input.c_str());
		cimg_forXYC(reflectance,x,y,c)
		{
			if (matteImg(x,y))
			{
				if (img_luminance(x,y,0,0) > 0.01*MAX_RANGE_LUM) reflectance(x,y,0,c)/=img_luminance(x,y,0,0);
				else reflectance(x,y,0,c)=0.0;
			}else { reflectance(x,y,0,c)=0.0; img_luminance(x,y,0,0) = 0;}
		}

		// discard spurious pixels. Be careful with this operations since may produce errors depending on the image
		double mean, variance;
		mean = computeMean(reflectance, matteImg, &variance);
		reflectance.cut(0,(mean + 3*sqrt(variance)));
		reflectance*=MAX_RANGE_LUM/reflectance.max();

		/* FINAL PRINT */
		reflectance.save(name_dst5);
		img_luminance.save(name_dst3);


	}

	time(&end);

	diff = difftime(end,start);

	printf("System Definition: --> Running time %.1f seconds\n", diff);


	return 0;
}

