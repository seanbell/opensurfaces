//----------------------------------------------------------------------
//	File:			normalizator.h
//	Author:			Adolfo Munoz and Elena Garces
//	Last modified:	18/07/2012
//	Description:	functions that build the system of equations
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

#ifndef _NORMALIZATOR_H_
#define _NORMALIZATOR_H_

#ifndef cimg_display
#define cimg_display 0
#endif

#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/symmetric.hpp>
//#include <boost/numeric/ublas/matrix_sparse.hpp>
#include <boost/numeric/ublas/io.hpp>
#include <boost/numeric/ublas/lu.hpp>

#include <algorithm>
#include <ctype.h>
#include <cmath>
#include <math.h>
#include <vector>
#include <list>
#include <iostream>
#include <cstdlib>
#include <iomanip>
#include <set>
#include <CImg.h>


#include "auxiliar.h"
#include "segmentacion.h"
#include "matte.h"
#include <qmr.h>


namespace Normalization {
#include "matrix.h"
#include "equation.h"
#include "equation-system.h"
#include "preconditioners.h"


//using namespace boost::numeric::ublas;
using namespace cimg_library;
using namespace Imaging;

class Normalizator
{
private:

	template<typename EdgeContainer>
	void build_matrix_ratios(vector<vector<double> >& matrixRatios, const Segmentacion& seg, CImg<double>& luminance,
		const EdgeContainer& edges)
	{
		int num_sets = int(seg.getListOfClusters().size());
		int width = luminance.width(); int height = luminance.height();
		ublas::matrix<int> pointsCounter(num_sets,num_sets);
		ublas::symmetric_matrix<int> edgesCounter(num_sets,num_sets);

		/* initialization of Ratio Matrix. Each ratio represents the relationship between two contiguous clusters.
		The index of the matrix are the id of each clusters. There is no ratio m[i][j] if i > j */
		for (int i=0; i < num_sets; i++)
		for (int j=0; j < num_sets; j++)
		{
			edgesCounter(i,j) = 0;
			pointsCounter(i,j) = 0;
			matrixRatios[i][j] = 0.0;
		}

		typename EdgeContainer::const_iterator i;
		for (i=edges.begin(); i != edges.end(); i++)
		{
			int xa = (*i).a % width; int ya = (*i).a / width;
			int xb = (*i).b % width; int yb = (*i).b / width;

			int aSeg = seg.getCluster(xa,ya); int bSeg = seg.getCluster(xb,yb);

			if (aSeg != bSeg)
			{
				/*order*/
				if (bSeg > aSeg)
				{
					std::swap(aSeg, bSeg);
					std::swap(xa,xb);
					std::swap(ya,yb);
				}
				edgesCounter(aSeg,bSeg)++;

				for (int ii = -3; ii <= (int) 3; ii++)
				for (int jj = -3; jj <= (int) 3; jj++)
				{
					if (((xa+ii) >= 0) && ((xa+ii) < width)  && ((ya+jj) >= 0) && ((ya+jj) < height))
					{
						if (seg.getCluster(xa+ii, ya+jj) ==  seg.getCluster(xa, ya))
						{
							pointsCounter(aSeg,bSeg)++;
							matrixRatios[aSeg][bSeg]+= *luminance.data(xa+ii, ya+jj,0,0);
						}
					}

					if (((xb+ii) >= 0) && ((xb+ii) < width)  && ((yb+jj) >= 0) && ((yb+jj) < height))
					{
						if ( seg.getCluster(xb+ii, yb+jj) ==  seg.getCluster(xb, yb))
						{
							pointsCounter(bSeg,aSeg)++;
							matrixRatios[bSeg][aSeg]+= *luminance.data(xb+ii, yb+jj,0,0);
						}
					}
				}

			}
		}


		for (int i=0; i < num_sets; i++)
		for (int j=0; j < num_sets; j++)
		{
			if (matrixRatios[i][j]!=0 && i!=j )
			{
				if (edgesCounter(i,j) >= 10)
					matrixRatios[i][j]/=pointsCounter(i,j);
				else matrixRatios[i][j]=0.0;
			}
		}


	}



	/**
		REGULARIZATION EQUATION: one equation
	*/
	template<typename System, typename real>
	void create_regularization_equations(System& equations, real weight = 1.0)
	{
		equations.add_equation(EquationLogCoefficientBalance<real>(weight));
	}


	/**
		REFLECTANCE EQUATIONS: ONE FOR EACH COLOR CHANNEL AND ONE FOR EACH PAIR OF SIMILAR REFLECTANCE CLUSTERS
	*/
	template<typename System, typename real>
	void create_reflectance_eq_equations(System& equations, const int i, const int j,
		double *media_clusteri, double *media_clusterj, double &lummediai, double &lummediaj, real weight = 10.0)
	{
		equations.add_equation(EquationLogReflectanceEq<real>(i,j,media_clusteri[0], media_clusterj[0], lummediai, lummediaj, weight));
		equations.add_equation(EquationLogReflectanceEq<real>(i,j,media_clusteri[1], media_clusterj[1], lummediai, lummediaj, weight));
		equations.add_equation(EquationLogReflectanceEq<real>(i,j,media_clusteri[2], media_clusterj[2], lummediai, lummediaj, weight));
	}


	/**
		LUMINANCE CONTINUITY EQUATIONS: one eq per each pair of neighbor clusters
	*/
	template<typename System, typename real>
	int create_matrix_ratios_equations(System& equations,const vector< vector<double> >& matrixRatios,
		real threshold = 0.1, real weight = 1.0)
	{
		int n_eq=0;
		int num_sets = int(matrixRatios.size());
		for (int i=0; i < num_sets; i++)
		for (int j=(i+1); j < num_sets; j++)

			if (matrixRatios.at(i).at(j) != 0 && matrixRatios.at(j).at(i)!= 0)
			{
				if (equations.add_equation(EquationLogClusterRatio<real>(i,j,matrixRatios.at(i).at(j),matrixRatios.at(j).at(i),threshold,weight))) n_eq++;
			}
		return n_eq;
	}

	/**
		BUILD THE LINEAR SYSTEM OF EQUATIONS
	*/
	template<typename System, typename EdgeContainer>
	void build_equations(System& equations, const Segmentacion& seg, CImg<double>& luminance, CImg<double>& input, const EdgeContainer& edges,
		vector< vector<double> > &matrixRatios, const vector<tpPair> *eqReflectance = NULL)
	{
		int n_eq;

		build_matrix_ratios(matrixRatios,seg,luminance,edges);

		/* LUMINANCE CONTINUITY EQUATIONS*/
		if (lum_cont_weight > 0.0)
		{
			n_eq = create_matrix_ratios_equations(equations,matrixRatios,equation_threshold,lum_cont_weight);
		}

		/* REFLECTANCE SIMILARITY EQUATIONS*/
		if (!eqReflectance->empty())
		{
			vector<est> medias_color;
			vector<double> medias_lum;

			CImg<double> aux1(input.get_channel(0)), aux2(input.get_channel(1)),  aux3(input.get_channel(2));
			CImg<double> aux4(luminance);

			for (unsigned int i=0; i < seg.getListOfClusters().size(); i++)
			{

				if (seg.getListOfClusters().at(i).getPixels().size() > 0)
				{
					est aux = computeMean(&aux1, &aux2, &aux3, seg.getListOfClusters().at(i).getPixels());
					medias_color.push_back(aux);
					medias_lum.push_back(computeMean(&aux4,seg.getListOfClusters().at(i).getPixels()));
				}
			}

			for (unsigned int l = 0; l< eqReflectance->size(); l++)
			{
				int i = eqReflectance->at(l).i;
				int j = eqReflectance->at(l).j;
				double aux_i[3], aux_j[3];

				aux_i[0] = medias_color[i].L;
				aux_i[1] = medias_color[i].a;
				aux_i[2] = medias_color[i].b;

				aux_j[0] = medias_color[j].L;
				aux_j[1] = medias_color[j].a;
				aux_j[2] = medias_color[j].b;

				create_reflectance_eq_equations(equations,i, j, aux_i,aux_j, medias_lum[i],medias_lum[j], 1.0);
			}


		}

		/* REGULARIZATION TERM*/
		create_regularization_equations(equations,regularization_weight);
	}



	/**
		SOLVE THE SYSTEM
	*/
	template<typename real>
	void solve_system(const Matrix<real>& A, const Vector<real>& B, Vector<real>& x)
	{
		PreconditionerSqrootDiagonal<real> prec(A);
		x.resize(B.size());
		// init x
		for (unsigned int i=0; i < B.size(); i++) x(i)=0.0;

		int ret = QMR(A, x, B, prec, prec, qmr_iterations, qmr_tolerance);

		if (ret==1) cout << "QMR did not converge to a solution with the specified tolerance and iterations" << endl;
		else if (ret!=0) cout << "QMR had a breakdown (whatever that is)" << endl;

	}

	/**
		SOLVE THE SYSTEM
	*/
	template<typename System, typename real>
	void solve_system(const System& equations, Vector<real>& x)
	{
		Matrix<double> A; Vector<double> B;
		equations.build_matrices(A,B);
		solve_system(A,B,x);
	}


	/**
		COMPUTE THE SHADING
	*/
	template<typename real>
	void apply_segment_exp_coefficients(const Vector<real>& coefficients, const Segmentacion& seg,CImg<double>& image, const MatteImage& matte)
	{
		cimg_forXYZC(image,x,y,z,c)
		{
			if ( matte(x,y) )
			{
				int segment = seg.getCluster(y*image.width() + x);
				image(x,y,z,c)*=exp(coefficients(segment));
			}
		}
	}

	/**
		INTERPOLATE BOUNDARIES
	*/
	template<typename EdgeContainer>
	void interpolateBoundaries(CImg<double> *nueva, const EdgeContainer& edges, const vector< vector<double> >& matrizRatios, const CImg<int> &labels, const vector<Cluster>& listaC, const Vector<double>& x)
	{

		int width = nueva->width(); int height = nueva->height();
		for (typename EdgeContainer::const_iterator i=edges.begin(); i != edges.end(); i++)
		{
			int xa = (*i).a % width; int ya = (*i).a / width;
			int xb = (*i).b % width; int yb = (*i).b / width;

			int aSeg = (labels)(xa,ya,0,0);	int bSeg = (labels)(xb,yb,0,0);

			if (bSeg > aSeg)
			{
				std::swap(aSeg, bSeg);
				std::swap(xa,xb);
				std::swap(ya,yb);
			}

			if (matrizRatios[aSeg][bSeg] != 0.0 && matrizRatios[bSeg][aSeg] != 0.0)
			{
					// paint cluster i
					if (xa < (width - 2) && xa >= 2 && ya < (height - 2) && ya >= 2)
						*nueva->data(xa,ya,0,0) = medianfilter(nueva, xa, ya);

					// paint cluster j
					if (xb < (width - 2) && xb >= 2 && yb < (height - 2) && yb >= 2)
						*nueva->data(xb,yb,0,0) = medianfilter(nueva, xb,yb);
				}

			}

			for(unsigned int i = 0; i < listaC.size(); i++)
			{
				if (fabs(x(i)) > 5.0)
				{
					vector<int> listOfPoints;

					for (unsigned int p = 0; p < listaC[i].getPixels().size(); p++)
					{

						int x = listaC[i].getPixels()[p] % width; int y = listaC[i].getPixels()[p] / width;
						if (x < (width - 2) && x >= 2 && y < (height - 2) && y >= 2)
							*nueva->data(x,y,0,0) = medianfilter(nueva, x, y);
					}
				}
			}
	}


	int qmr_iterations;
	double qmr_tolerance;
	double lum_cont_weight;
	double regularization_weight;
	double reflectance_weight;
	double equation_threshold;
	enum EquationSystemMode { ON_THE_FLY};
	EquationSystemMode equation_system_mode;


public:

	/**
		CONSTRUCTOR
	*/
	Normalizator(int _qmr_iterations = 1000,double _qmr_tolerance = 0.000000000000001,
		double _lum_cont_weight = 1.0, double _regularization_weight = 1.0,
		double _reflectance_weight=1.0,double _equation_threshold=1.e-4,
		EquationSystemMode _equation_system_mode=ON_THE_FLY):
			qmr_iterations(_qmr_iterations),qmr_tolerance(_qmr_tolerance),
			lum_cont_weight(_lum_cont_weight),
			regularization_weight(_regularization_weight),
			reflectance_weight(_reflectance_weight),
			equation_threshold(_equation_threshold),
			equation_system_mode(_equation_system_mode)
		{ }

	/**
		CONSTRUCTOR	FROM COMMAND LINE
	*/
	Normalizator(int argc,char** argv):qmr_iterations(1000),qmr_tolerance(0.000000000000001),
		lum_cont_weight(1.0),regularization_weight(1.0),reflectance_weight(0.0),
		equation_threshold(1.e-4), equation_system_mode(ON_THE_FLY)
	{
		// for (int i=0;i<argc;i++)
		// {
			// if (i < argc - 1)
			// {
				// /*no options*/
			// }
		// }
	}

	/**
		BUILD AND SOLVE THE SYSTEM OF EQUATIONS
	*/
	template <typename real>
	void normalize(const Segmentacion& seg, CImg<real>& luminance, CImg<real>& input, const MatteImage& matte,
		vector<tpPair> *eqReflectance=NULL)
	{

		list<edge> edges;
		buildGraph(edges, luminance, 2, matte);

		int num_sets = int(seg.getListOfClusters().size());
		vector< vector<real> > matrixRatios(num_sets, vector<real>(num_sets,0.0));
		Vector<real> x;
		switch (equation_system_mode) {
			case ON_THE_FLY:
			{
				#ifdef VERBOSE
					cout << "System Definition: --> Filling the matrices" << endl;
				#endif
				EquationSystemOnTheFly<real> equations(num_sets);
				build_equations(equations,seg,luminance,input,edges,matrixRatios,eqReflectance);
				#ifdef VERBOSE
					cout << "System Definition: --> Solving the system" << endl;
				#endif
				solve_system(equations,x);
			}
			break;

		};

		apply_segment_exp_coefficients(x,seg,luminance,matte);
		interpolateBoundaries(&luminance, edges, matrixRatios, seg.imageMapLabels, seg.getListOfClusters(),x);
	}




};



}; //namespace Normalization



#endif // _NORMALIZATOR_H_
