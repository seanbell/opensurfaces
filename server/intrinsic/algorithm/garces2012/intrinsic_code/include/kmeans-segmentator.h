//----------------------------------------------------------------------
//	File:			segmentation.h
//	Author:			Elena Garces and Adolfo Munoz
//	Last modified:	18/07/2012
//	Description:	functions to control the kmeans clustering
//					It needs the library KMlocal
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

#ifndef _KMEANS_SEGMENTATOR_H_
#define _KMEANS_SEGMENTATOR_H_

#include "segmentacion.h"
#include "matte.h"
#include "KMlocal.h"			// k-means algorithms
using namespace Imaging;
namespace Imaging {
namespace Segment {

class KMeansSegmentator
{
	KMterm	term;		
	int k;		// number of centers
	float position_weight;

public:

	void set_k(int _k) { k=_k; }
	void set_stages(int s) { term.setAbsMaxTotStage(s);	}
	void set_position_weight(float pw) { position_weight = pw; }


	//----------------------------------------------------------------------
	//  Termination conditions
	//	These are explained in the file KMterm.h and KMlocal.h.  Unless
	//	you are into fine tuning, don't worry about changing these.
	//----------------------------------------------------------------------
	KMeansSegmentator(int _k=10, int _stages=1000, float _position_weight = 0.0):
			term(100, 0, 0, 0,	// run for 100 stages
			0.10,			// min consec RDL
			0.10,			// min accum RDL
			3,			// max run stages
			0.50,			// init. prob. of acceptance
			10,			// temp. run length
			0.95),			// temp. reduction factor
			k(_k),
			position_weight(_position_weight)
		{	term.setAbsMaxTotStage(_stages);		}

	void set(int argc, char** argv, string& name_output)
	{
		for (int i=1;i<argc;i++)
		{
			if ((argv[i][0]=='-')&&(i<argc-1))
			{
			    if (strcmp("-km-k",argv[i])==0) k=atoi(argv[++i]); 				
			}
		}
		ostringstream convert;   // stream used for the conversion
		convert << "_k" << k;      // insert the textual representation of 'Number' in the characters in the stream
		name_output.append(convert.str());		
	}

	template <typename Tinput, typename Tmatte> 
	void segmentate(const CImg<Tinput>& input, Segmentacion& segmentation, const Tmatte& matte) const
	{
			
		int nPoints=input.spectrum();	
		if (position_weight!=0) nPoints+=2;
		KMdata dataPts(nPoints, input.width()*input.height());		// allocate data storage
		int p = 0;
		cimg_forXY(input,x,y) {
			if (matte(x,y))
			{ 
				cimg_forC(input,c) dataPts[p][c] = 10000.*input(x,y,0,c);
				if (position_weight > 0.0)
				{
					dataPts[p][nPoints-2]=position_weight*float(x)/float(input.width());
					dataPts[p][nPoints-1]=position_weight*float(y)/float(input.width());
				}
			}
			else for (int c = 0;c<nPoints;c++) dataPts[p][c] = 0.0f;
			p++;
		}

		dataPts.setNPts(input.width()*input.height()); // set actual number of pts
		dataPts.buildKcTree();			// build filtering structure
		KMfilterCenters ctrs(k, dataPts);		// allocate centers
		KMlocalHybrid kmHybrid(ctrs, term);		// Hybrid heuristic
		ctrs = kmHybrid.execute();

		KMctrIdxArray closeCtr = new KMctrIdx[dataPts.getNPts()];
		double* sqDist = new double[dataPts.getNPts()];
		ctrs.getAssignments(closeCtr, sqDist);

		p = 0;
		cimg_forXY(input,x,y)
		{
			if (matte(x,y))
				segmentation.setCluster(x,y,closeCtr[p]+1);
			else
				segmentation.setCluster(x,y,BACKG_CLUSTER);
			p++;
		}
	}

	template <typename Tinput> 
	void segmentate(const CImg<Tinput>& input, Segmentacion& segmentation) const
	{
		this->segmentate(input,segmentation,MatteAll());
		
	}

};

};
};

#endif
