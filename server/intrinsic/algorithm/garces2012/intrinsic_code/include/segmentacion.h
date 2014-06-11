//----------------------------------------------------------------------
//	File:			segmentation.h
//	Author:			Elena Garces and Adolfo Munoz
//	Last modified:	18/07/2012
//	Description:	funcions that control the clustering
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


#ifndef SEGMENTACION
#define SEGMENTACION

#include <vector>
#include <iostream>
#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/symmetric.hpp>
#include <boost/numeric/ublas/io.hpp>
#include <boost/numeric/ublas/lu.hpp>


#define cimg_OS 1
#define cimg_display 0
#define cimg_plugin2 <../lib/CImg/cimg-additions.h>
#include "CImg.h"

#include "auxiliar.h"
#include "matte.h"


using namespace cimg_library;
namespace ublas = boost::numeric::ublas;
using namespace std;


class Cluster {

public:

	Cluster(){}
	Cluster(int id):idCluster(id){}
	Cluster(int id, vector<int> p):idCluster(id),pixels(p){}

	Cluster(int id, int punto):idCluster(id){pixels.push_back(punto);}


	const vector<int>& getPixels() const {return pixels;}
	vector<int>& getPixels() {return pixels;}

	void addPixel(int p) {pixels.push_back(p);}

	void addPixel(vector<int> lista)
	{
		if (!lista.empty())
		{
			pixels.insert(pixels.end(), lista.begin(), lista.end());

		}
	}


	unsigned int size() { return pixels.size();}

	int idCluster;
	vector<int> pixels;

	int numPixels;
};



class Segmentacion {


public:

	int segMode;
	float percent_grad_max;

	CImg<int> imageMapLabels;
	vector<Cluster> listOfClusters;

	float lum_th_max;
	float lum_th_min;
	float croma_th_min;



	Segmentacion (int width= 1, int height=1,
		float _lum_th_max=95., float _lum_th_min=15., float _croma_th_min=20.,
		int _seg_mode=KMEANS_SEG, float _percent_grad=0.01):

		imageMapLabels(width,height,1,1),
		lum_th_max(_lum_th_max), lum_th_min(_lum_th_min), croma_th_min(_croma_th_min),
		segMode(_seg_mode),
		percent_grad_max(_percent_grad) {}



	void set(int argc, char** argv)
	{
		int i = 1;
		while (i < argc)	// read arguments
		{
			if (!strncmp(argv[i],"-th",3))
			{
			    if (!strcmp("-th-lum-max",argv[i])) lum_th_max= (float) atof(argv[++i]);
				else if (!strcmp("-th-lum-min",argv[i])) lum_th_min= (float) atof(argv[++i]);
				else if (!strcmp("-th-cr-min",argv[i])) croma_th_min=(float) atof(argv[++i]);

			}
			else if (!strcmp(argv[i], "-seg-mode"))
			{
				if (!strcmp(argv[i+1], "KMEANS")) {segMode = KMEANS_SEG; i++;}
				else if (!strcmp(argv[i+1], "FILE"))
				{
					segMode = FILE_SEG; i++;
					if (FileExists(argv[i+1]))
					{
						CImg<int> labels_aux(argv[++i]);
						labels_aux-=1;
						imageMapLabels.assign(labels_aux);
						updateLabels();
					}
					else
					{
						cerr << "Unrecognized file.\n" << argv[i+1];
						exit(1);
					}
				}
			}
			else if (!strcmp(argv[i], "-porc_grad")) 	percent_grad_max = atof(argv[++i]);
			i++;
		}
	}



	void setCluster(int x, int y, int val)
	{
		if ((x>=0) && (x<imageMapLabels.width()) && (y>=0) && (y<imageMapLabels.height()))
			*imageMapLabels.data(x, y, 0,0) = val;
	}

	void setCluster(int p, int val)
	{
		int width = imageMapLabels.width();
		int x = p % width;
		int y = p / width;
		if ((x>=0) && (x<width) && (y>=0) && (y<imageMapLabels.height()))
			*imageMapLabels.data(x, y, 0,0) = val;
	}


	void setListOfClusters(vector<Cluster> c) { listOfClusters = c; }


	/**
	   @return segment of the pixel (p)
	 */
	int getCluster(int p) const
	{
		int x = p % width();
		int y = p / width();

		if ((x >= 0 && x < width()) && (y >= 0 && y < height()) )
			return *imageMapLabels.data(x, y, 0,0);//mapeo[x][y];
		else return OUT_OF_RANGE;
	}
	/**
	   @return segment of the pixel (x,y)
	 */
	int getCluster(int x, int y) const
	{
		if ((x >= 0 && x < width()) && (y >= 0 && y < height()) )
			return *imageMapLabels.data(x, y, 0,0);//mapeo[x][y];
		else return OUT_OF_RANGE;
	}


	/**
	   @return listOfClusters of the image
	 */
	const vector<Cluster>& getListOfClusters() const { return listOfClusters; }
	vector<Cluster>& getListOfClusters() { return listOfClusters; }
	unsigned int nclusters() { return listOfClusters.size(); }
	int width() const { return imageMapLabels.width(); }
	int height() const { return imageMapLabels.height(); }


	/**
	   Rebuild the list of the clusters from the labelMap
	  */
	void updateLabels();


	/*--------------------------------- FILTERS ---------------------------------*/
	Segmentacion get_separate_noncontiguous_clusters();
	void mergeSmallClusters(const CImg<double>& image, int max_it, int max_size_clus, float percent_external);
	int mergeSmoothBoundaries(CImg<double> *im_input, const MatteImage& matte, vector<tpPair> &paresR);

	/*--------------------------------- REFLECTANCE PAIRS ---------------------------------*/
	vector<tpPair> searchPairsRcte(Segmentacion& seg_old);
	void updateReflectancePairs(vector<tpPair>& eqReflectancenew, CImg<double> *luminance, int MIN_SIZE_CLUS=100);




	/*--------------------------------- FUNCTIONS TO PAINT THE OUTPUT ---------------------------------*/
	/**
	 * Take an image and colorize it according to the segmentation.
    */
	template<typename T>
	void colorize_mean(CImg<T>& image)
	{
		image.resize(this->width(),this->height());
		CImg<T> color_table(this->nclusters()+1,1,image.depth(),image.spectrum());
		color_table.fill(0);
		std::vector<unsigned int> npixels(this->nclusters()+1,0);

		cimg_forXY(imageMapLabels,x,y)
		{
			unsigned int clus = getCluster(x,y);
			npixels[clus]++;
			if (clus>0) cimg_forZC(image,z,c)
			{
				color_table(clus,0,z,c) += image(x,y,z,c);
			}
		}

		cimg_forXY(imageMapLabels,x,y)
		{
			unsigned int clus = getCluster(x,y);
			cimg_forZC(image,z,c)
			{
				image(x,y,z,c) = color_table(clus,0,z,c)/T(npixels[clus]);
			}
		}
	}

	template<typename T>
	void colorize_coherent(CImg<T>& image)
	{

		colorize_mean(image);
		image.normalize(T(0),T(1));
		image.RGBtoHSV();
		cimg_forXYZ(image,x,y,z)
		{
			image(x,y,z,0) = 2.0*image(x,y,z,0) + 120.0; while (image(x,y,z,0)>T(360)) image(x,y,z,0)-= T(360);
			image(x,y,z,1) = 2.0*image(x,y,z,2) + 0.5; while (image(x,y,z,1)>T(1)) image(x,y,z,1)-= T(1);
			image(x,y,z,2) = 3.0*image(x,y,z,1); while (image(x,y,z,2)>T(1)) image(x,y,z,2)-= T(1);
		}
		image.HSVtoRGB();
		image.normalize(T(0),T(255));
	}

	/**
	 * Take an image and colorize it according to the segmentation.
         */
	template<typename T>
	void colorize_random(CImg<T>& image, int min, int max)
	{
		//MersenneRNG random(3);
		srand(3);
		image.resize(this->width(),this->height());
		CImg<T> color_table(this->nclusters()+1,1,image.depth(),image.spectrum());

		cimg_forXYZC(color_table,x,y,z,c)
		{
			//color_table(x,y,z,c) = min + (max-min)*random();
			color_table(x,y,z,c) = rand() % max ;
		}

		cimg_forXY(imageMapLabels,x,y)
		{
			unsigned int clus = getCluster(x,y);
			cimg_forZC(image,z,c)
			{
				image(x,y,z,c) = color_table(clus,0,z,c);
			}
		}
	}

	/**
	 * Take an image and colorize it according to the segmentation.
         */
	template<typename T>
	void colorize_hybrid(CImg<T>& image, float randomness)
	{
		//MersenneRNG random(3);
		colorize_mean(image);
		CImg<T> hsv_displacement(this->nclusters()+1,1,1,1);
		cimg_forX(hsv_displacement,x)
		{
			hsv_displacement(x,0,0,0) = 120.0 + randomness*360.0*rand();
//			hsv_displacement(x,0,0,1) = randomness*random();
//			hsv_displacement(x,0,0,2) = randomness*random();
		}

		CImg<T> hsv_factor(this->nclusters()+1,1,1,1);
		cimg_forX(hsv_factor,x)
		{
			hsv_factor(x,0,0,0) = (1.0 + randomness*rand());
//			hsv_factor(x,0,0,1) = (1.0 + randomness*random());
//			hsv_factor(x,0,0,2) = (1.0 + randomness*random());
		}

		image.RGBtoHSV();
		cimg_forXY(image,x,y)
		{
			unsigned int clus = getCluster(x,y);
			cimg_forZ(image,z)
			{
				image(x,y,z,0)*=hsv_factor(clus,0,0,0);
				image(x,y,z,0)+=hsv_displacement(clus,0,0,0);
				while (image(x,y,z,0)>T(360)) image(x,y,z,0)-= T(360);
//				image(x,y,z,1) = hsv_factor(clus,0,0,1)*image(x,y,z,1) + hsv_displacement(clus,0,0,1);
//				while (image(x,y,z,1)>T(1)) image(x,y,z,1)-= T(1);
//				image(x,y,z,2) = hsv_factor(clus,0,0,2)*image(x,y,z,2) + hsv_displacement(clus,0,0,2);
//				while (image(x,y,z,2)>T(1)) image(x,y,z,2)-= T(1);
			}
		}
		image.HSVtoRGB();
	}


	private:

		int detectSpurious(const CImg<double>& image, int max_size_clus, float percent_external);
		void scanline(unsigned int coriginal, unsigned int cnew, int x, int y, Segmentacion& sol);
		int mergeSegment(const CImg<double>& image, int pos, int min_size_clus);
};



#endif
