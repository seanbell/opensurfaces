//----------------------------------------------------------------------
//	File:			segmentation.cpp
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

#include "segmentacion.h"
#include "auxiliar.h"

#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/symmetric.hpp>

#include <algorithm>
#include <list>
#include <iostream>
#include <fstream>
#include "CImg.h"
using namespace std;
using namespace cimg_library;



/*-------------------------------------------------------------------------------------------------*/
void Segmentacion::updateLabels()
/*-------------------------------------------------------------------------------------------------*/
{

	int width = this->imageMapLabels.width();
	int height = this->imageMapLabels.height();

	vector<Cluster> newClusters;
	vector<int> founds;

	cimg_forXY(imageMapLabels,x,y)
	{

		int comp = *imageMapLabels.data(x,y,0,0);
		if ( comp != BACKG_CLUSTER )
		{
			vector<int>::iterator i = find(founds.begin(), founds.end(), comp);

			if (i == founds.end())
			{
				/* add */
				founds.push_back(comp);
				*imageMapLabels.data(x,y,0,0) = int(founds.size())-1;
				Cluster nuevo(comp, y*width+x);
				newClusters.push_back(nuevo);
			}
			else
			{
				/* already exists, update*/
				int index = std::distance (founds.begin(), i );
				*imageMapLabels.data(x,y,0,0) = index;
				newClusters[index].addPixel(y*width+x);


			}
		}
	}
	setListOfClusters(newClusters);
}




int Segmentacion::mergeSegment(const CImg<double>& image, int pos, int min_size_clus)
{

	int width = image.width();
	int n_changes=0;

	vector<int> pixels = getListOfClusters()[pos].getPixels();

	int idSetCentral = getListOfClusters()[pos].idCluster;

	for (int p = 0; p < (int) pixels.size(); p++)
	{
		int x = pixels[p] % width;	int y = pixels[p] / width;
		int idMostSimilar=-1;
		double diffMostSimilar=10000000.;

		int dist = 1;
		for (int j = y-dist; j <= y+dist; j++) {
			for (int i = x-dist; i <= x+dist; i++) {

				int set = getCluster(i,j);
				if (set >= 0 && set != idSetCentral && getListOfClusters().at(*imageMapLabels.data(i,j,0,0)).size() >= min_size_clus)
				{
					double squaredDiff = 0.0;
					cimg_forC(image,c) squaredDiff += pow(image(i, j,0,c) -  image(x, y,0,c), 2);
					squaredDiff=sqrt(squaredDiff);


					if (squaredDiff < diffMostSimilar)
					{
						diffMostSimilar = squaredDiff;
						idMostSimilar = set;
					}
				}
			}
		}
		if (idMostSimilar >=0)
		{
			n_changes++;
			setCluster(x, y, idMostSimilar);
		}
	}
		return n_changes;
}


/*-------------------------------------------------------------------------------------------------*/
/*  */

int Segmentacion::detectSpurious(const CImg<double>& image, int max_size_clus, float percent_external)
/*-------------------------------------------------------------------------------------------------*/
{
	int total_changes=0;

	int width = image.width();
	for (int k = 0; k < (int) listOfClusters.size(); k++)
	{
		if (listOfClusters[k].getPixels().size() < max_size_clus)
		{
			vector<int> pixels = listOfClusters[k].getPixels();
			int votesBoundary = 0;
			for (int p = 0; p < (int) pixels.size(); p++)
			{
				int x = pixels[p] % width;
				int y = pixels[p] / width;
				int idSetCentral = getCluster(x,y); /* id del conjunto del pixel central */

				if ( (getCluster(x-1, y) >= 0 && getCluster(x-1, y) != idSetCentral) ||
					(getCluster(x+1, y) >= 0 && getCluster(x+1, y) != idSetCentral) ||
					(getCluster(x, y+1) >= 0 && getCluster(x, y+1) != idSetCentral) ||
					(getCluster(x, y-1) >= 0 && getCluster(x, y-1) != idSetCentral))
					votesBoundary++;
			}

			if (votesBoundary >= percent_external * pixels.size())
			{
				int changes = mergeSegment(image, k, max_size_clus);
				total_changes+=changes;
			}
		}
	}

	return total_changes;
}



void Segmentacion::mergeSmallClusters(const CImg<double>& image, int max_it,
								   int max_size_clus, float percent_external)
{
	int n_changes = 1; 	int it = 1;
	while (it < max_it && n_changes > 0)
	{
		n_changes = detectSpurious(image, max_size_clus, percent_external);
		#ifdef VERBOSE
		cout << "Clustering: --> \t\tIteration  " << it << " changes " << n_changes << endl;
		#endif
		updateLabels();
		it++;
	}
}



template <typename matrizBoost>
void analysis_gradient_clusters(matrizBoost& matrixRatios, const Segmentacion& seg,
			const CImg<double>& input, const MatteImage& matte)
	{
		int num_sets = int(seg.getListOfClusters().size());
		list<edge> edges;
		ublas::symmetric_matrix<int> edges_counter(num_sets,num_sets);

		for (int i=0; i < num_sets; i++)
			for (int j=i; j < num_sets; j++)
			{
				edges_counter(i,j) = 0;
				matrixRatios(i,j) = 0.0;
			}

		for (int i=0; i < num_sets; i++)
			matrixRatios(i,i) = 0.0;


		buildGraph(edges, input, 2, matte);
		for (list<edge>::const_iterator i=edges.begin(); i != edges.end(); i++)
		{
			int aSeg = seg.getCluster((*i).a);
			int bSeg = seg.getCluster((*i).b);

			if (aSeg != bSeg && aSeg >= 0 && bSeg >= 0)
			{
				int xa = (*i).a % input.width();
				int ya = (*i).a / input.width();
				int xb = (*i).b % input.width();
				int yb = (*i).b / input.width();

				double diffgrad =0.0;
				cimg_forC(input,c)
				{
					diffgrad+= fabs(input(xa, ya,0,c) - input(xb, yb,0,c));
				}
				diffgrad/=input.spectrum();


				if (aSeg <= bSeg)
				{
					edges_counter(aSeg,bSeg)++;
					matrixRatios(aSeg,bSeg)+=diffgrad;
				} else
				{
					edges_counter(bSeg,aSeg)++;
					matrixRatios(bSeg,aSeg)+=diffgrad;
				}
			}
		}

		for (int i=0; i < num_sets; i++)
			for (int j=(i+1); j < num_sets; j++)
			{
				if (matrixRatios(i,j)!=0)
				{
					if (edges_counter(i,j) > 15)
						matrixRatios(i,j)/=edges_counter(i,j);
					else matrixRatios(i,j)=0.0;
				}
			}
	}


bool func_ord_e(const edge &a, const edge &b)
	{ return (a.w < b.w);}


int Segmentacion::mergeSmoothBoundaries(CImg<double> *im_input, const MatteImage &matte, vector<tpPair> &paresR)
{

	int width = im_input->width();
	int height = im_input->height();


	for (unsigned int p=0; p < paresR.size(); p++)
	{
		paresR[p].i= imageMapLabels( paresR[p].i % im_input->width(), paresR[p].i / im_input->width(),0,0);
		paresR[p].j= imageMapLabels( paresR[p].j % im_input->width(), paresR[p].j / im_input->width(),0,0);
	}


	float max_grad = percent_grad_max*im_input->max();


	/* MERGE, ANALYZING GRADIENTS */
	int num_sets = int(getListOfClusters().size());
	ublas::symmetric_matrix<float> matrixRatios(num_sets,num_sets);
	analysis_gradient_clusters(matrixRatios, *(this),*im_input,matte);

	vector<edge> edges;

	int n=0;
	for (int i=0; i < num_sets; i++)
		for (int j=(i+1); j < num_sets; j++)
		{
			if (matrixRatios(i,j) != 0)
			{
				double diff=matrixRatios(i,j);
				if (diff  < max_grad)
					edges.push_back(edge(i,j,diff));
			}
		}


	std::sort(edges.begin(), edges.end(), func_ord_e);

	vector<bool> tratados(getListOfClusters().size(),false);
	vector<bool> referenciado(getListOfClusters().size(),false);

	int n_changes=0;
	for (vector<edge>::const_iterator i=edges.begin(); i != edges.end(); i++)
	{
		int peq, grand;
		if (getListOfClusters()[(*i).a].size() < getListOfClusters()[(*i).b].size())
		{
			peq = (*i).a;
			grand = (*i).b;
		} else  {
			peq = (*i).b;
			grand = (*i).a;
		}

		if (tratados[grand] == false)
		{

			n_changes++;
			// remove the smaller cluster
			for (unsigned int p=0; p < getListOfClusters()[peq].size(); p++)
			{
				setCluster(getListOfClusters()[peq].getPixels()[p], grand);
			}
			tratados[peq]=true;
			listOfClusters[grand].addPixel(listOfClusters[peq].getPixels());

			for (unsigned int i=0; i < paresR.size(); i++)
			{
				if (paresR[i].valid && (paresR[i].i==peq || paresR[i].j == peq))
				{
					paresR[i].valid=false;
				}
			}
		}
	}

	vector<tpPair> paresRnew;
	for (unsigned int i=0; i < paresR.size(); i++)
	{
			if (paresR[i].valid)
			{
				tpPair aux;
				aux.i = getListOfClusters()[paresR[i].i].getPixels()[0];
				aux.j = getListOfClusters()[paresR[i].j].getPixels()[0];
				aux.valid = true;
				paresRnew.push_back(aux);
			}

	}
	paresR = paresRnew;
	updateLabels();

	//* --------------------------------------------------*/


	return n_changes;



}


void Segmentacion::updateReflectancePairs(vector<tpPair>& eqReflectance,  CImg<double> *luminance, int MIN_SIZE_CLUS)
{
	vector<tpPair> eqReflectancenew;
	float MIN_VARIATION_L = (float) 0.07*luminance->max();


	if (eqReflectance.size() > 0)
	{
		vector<float> averageLuminance(getListOfClusters().size(), -1);
		int index=0;
		for (unsigned int i=0; i < eqReflectance.size(); i++)
		{
			tpPair aux;
			aux.valid=true;
			aux.i = imageMapLabels(eqReflectance[i].i % width(),eqReflectance[i].i / width(),0,0);
			aux.j = imageMapLabels(eqReflectance[i].j % width(),eqReflectance[i].j / width(),0,0);

			if (aux.i > aux.j) std::swap(aux.i, aux.j);

			if (aux.i != aux.j && getListOfClusters().at(aux.i).size() > MIN_SIZE_CLUS && getListOfClusters().at(aux.j).size() > MIN_SIZE_CLUS)
			{
				averageLuminance[aux.i] = (averageLuminance[aux.i] < 0) ? computeMean(luminance, getListOfClusters().at(aux.i).getPixels()) : averageLuminance[aux.i];
				averageLuminance[aux.j] = (averageLuminance[aux.j] < 0) ? computeMean(luminance, getListOfClusters().at(aux.j).getPixels()) : averageLuminance[aux.j];

				if (averageLuminance[aux.i]  > 0 && averageLuminance[aux.j] > 0)
				{
					double diff = fabs(averageLuminance[aux.i]-averageLuminance[aux.j]);
					if (diff < MIN_VARIATION_L)	eqReflectancenew.push_back(aux);

				}
			}
		}

	}

	eqReflectance=eqReflectancenew;

}


vector<tpPair> Segmentacion::searchPairsRcte(Segmentacion& seg_old)
{

	vector<tpPair> pairsReflectance;
	vector< vector<int> > vec(seg_old.getListOfClusters().size(), vector<int>(0));
	for (unsigned int s = 0; s < getListOfClusters().size(); s++)
	{
		int p = getListOfClusters()[s].getPixels()[0];
		int clus_old=seg_old.getCluster(p);
		if (getListOfClusters()[s].getPixels().size() > 100)
			vec[clus_old].push_back(s);
	}

	for (unsigned int s = 0; s < vec.size(); s++)
	{
		for (unsigned int subS = 0; subS < vec[s].size(); subS++)
		{

			for (unsigned int sS = subS+1; sS < vec[s].size(); sS++)
			{
				int clusa=vec[s][subS];
				int clusb=vec[s][sS];

				tpPair aux;
				aux.i = getListOfClusters()[clusa].getPixels()[0];
				aux.j = getListOfClusters()[clusb].getPixels()[0];

				pairsReflectance.push_back(aux);
			}
		}
	}

	return pairsReflectance;
}



void Segmentacion::scanline(unsigned int coriginal, unsigned int cnew, int x, int y, Segmentacion& sol)
{
	int x2;

	if (getCluster(x,y) != BACKG_CLUSTER)
	{
		for (x2 = x; (getCluster(x2,y)==coriginal);x2++)	sol.setCluster(x2,y,cnew);

		for (x2 = (x - 1); (getCluster(x2,y)==coriginal);x2--) sol.setCluster(x2,y,cnew);

		for (x2 = (x - 1); (sol.getCluster(x2,y)==cnew) && (getCluster(x2,y)==coriginal);x2--)
		{
			if ( (sol.getCluster(x2,y-1)==NON_ASIGN) && (getCluster(x2,y-1)==coriginal) ) scanline(coriginal,cnew,x2,y-1,sol);
			if ( (sol.getCluster(x2,y+1)==NON_ASIGN) && (getCluster(x2,y+1)==coriginal) ) scanline(coriginal,cnew,x2,y+1,sol);
		}
		for (x2 = x; (sol.getCluster(x2,y)==cnew) && (getCluster(x2,y)==coriginal);x2++)
		{
			if ( (sol.getCluster(x2,y-1)==NON_ASIGN) && (getCluster(x2,y-1)==coriginal) ) scanline(coriginal,cnew,x2,y-1,sol);
			if ( (sol.getCluster(x2,y+1)==NON_ASIGN) && (getCluster(x2,y+1)==coriginal) ) scanline(coriginal,cnew,x2,y+1,sol);
		}

		for (x2 = (x - 1); (sol.getCluster(x2,y)==cnew) && (getCluster(x2,y)==coriginal);x2--)
		{
			if ( (sol.getCluster(x2+1,y-1)==NON_ASIGN) && (getCluster(x2+1,y-1)==coriginal) ) scanline(coriginal,cnew,x2+1,y-1,sol);
			if ( (sol.getCluster(x2-1,y-1)==NON_ASIGN) && (getCluster(x2-1,y-1)==coriginal) ) scanline(coriginal,cnew,x2-1,y-1,sol);

			if ( (sol.getCluster(x2+1,y+1)==NON_ASIGN) && (getCluster(x2+1,y+1)==coriginal) ) scanline(coriginal,cnew,x2+1,y+1,sol);
			if ( (sol.getCluster(x2-1,y+1)==NON_ASIGN) && (getCluster(x2-1,y+1)==coriginal) ) scanline(coriginal,cnew,x2-1,y+1,sol);

		}

		for (x2 = x; (sol.getCluster(x2,y)==cnew) && (getCluster(x2,y)==coriginal);x2++)
		{
			if ( (sol.getCluster(x2+1,y-1)==NON_ASIGN) && (getCluster(x2+1,y-1)==coriginal) ) scanline(coriginal,cnew,x2+1,y-1,sol);
			if ( (sol.getCluster(x2-1,y-1)==NON_ASIGN) && (getCluster(x2-1,y-1)==coriginal) ) scanline(coriginal,cnew,x2-1,y-1,sol);

			if ( (sol.getCluster(x2+1,y+1)==NON_ASIGN) && (getCluster(x2+1,y+1)==coriginal) ) scanline(coriginal,cnew,x2+1,y+1,sol);
			if ( (sol.getCluster(x2-1,y+1)==NON_ASIGN) && (getCluster(x2-1,y+1)==coriginal) ) scanline(coriginal,cnew,x2-1,y+1,sol);

		}
	} else sol.setCluster(x,y,BACKG_CLUSTER);
}

Segmentacion Segmentacion::get_separate_noncontiguous_clusters()
{
	Segmentacion sol(width(),height());
	sol.imageMapLabels.fill(NON_ASIGN);
	unsigned int cnew = 0;
	int x=0, y=0;

	while (y<height())
	{
		while ( (sol.getCluster(x,y)!=NON_ASIGN) && (y<height()) )
		{
			x++;
			if (x>=width()) { x = 0; y++;}
		}

		if (y<height())	scanline(getCluster(x,y),cnew,x,y,sol);
		cnew++;
	}
	return sol;
}

