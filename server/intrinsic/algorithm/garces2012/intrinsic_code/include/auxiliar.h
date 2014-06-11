//----------------------------------------------------------------------
//	File:			auxiliar.h
//	Author:			Elena Garces
//	Last modified:	18/07/2012
//	Description:	auxiliar functions
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
//    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
////----------------------------------------------------------------------

#ifndef AUXILIAR_H
#define AUXILIAR_H


#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <fstream>
#include <string>
#include <sys/stat.h>
#include <cstdlib>
#include <vector>
#include <list>
#include <cmath>

#include "matte.h"
using namespace Imaging;

#include "CImg.h"
using namespace cimg_library;
using namespace std;

#define NON_ASIGN -2
#define BACKG_CLUSTER -1
#define OUT_OF_RANGE -3

#define MAX_RANGE_LUM 65535

#define THRESHOLD(size, c) (c/size)

#define KMEANS_SEG 0
#define FILE_SEG 1


// general parameters of the algorithm
struct gral_params {

	string		name_input;
	string		name_mask;
	string		name_output;

	bool gammaCorrect;
	bool useRsimPairs;
	bool system_definition;

};



class edge 
{
	public:
		int a, b;
		double w_kk;
		double w;
		edge(int _a = -1, int _b = -1, double _w = 1.0): a(_a),b(_b),w(_w) { }
		/* 
		* Operator < for edges
		 */
		friend bool operator<(const edge &a, const edge &b)
		{
			return ((a.w != b.w) ? (a.w < b.w): (a.a < b.a) || ((a.a == b.a) && (a.b < b.b)));
		}

		
};


struct est {
	double L;
	double a;
	double b;
};


class tpPair 
{
	public:
		int i, j;
		bool valid;
		tpPair(int _i = -1, int _j = -1): i(_i),j(_j) { }

		friend bool operator==(const tpPair &a, const tpPair &b)
		{
			return ((a.i == b.i) && (a.j == b.j));
		}
};

/**
    Read arguments from the command line
*/
gral_params getArgs(int argc, char **argv);

/**
	Build the name of the output depending on the params
*/
string build_name_output(gral_params param, int segMode);

/**
    @return true if file exists
*/
bool FileExists(const char* strFilename);

/**
    @return mean and optionally variance of the one-color-channel image im
*/
double computeMean(const CImg<double> &im, const MatteImage& matte, double *variance=NULL);

/**
    @return mean of the points in listPoints of the three color channels images (c1,c2,c3)
*/
est computeMean(CImg<double> *c1, CImg<double> *c2, CImg<double> *c3, vector<int> listPoints);

/**
    @return mean of the points in listPoints
*/
double computeMean(CImg<double> *im, vector<int> listPoints);

/**
    @return median filter of 5x5 around pixels x,y
*/
double medianfilter(CImg<double> *original, int x, int y);

/**
    Builds a grid graph with the same size as image.
	Returns the list of edges
*/
int buildGraph(list<edge>& edges,const CImg<double>& image, int max_dist, const MatteImage& matte);
#endif
