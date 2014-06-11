#########################################################################
#                                                                       #
#    GC_optimization - software for energy minimization with graph cuts #
#                        Version 1.1                                    #
#    http://www.csd.uwo.ca/faculty/olga/software.html                   #
#                                                                       #
#    Copyright 2005 Olga Veksler (olga@csd.uwo.ca)                      #
#                                                                       #
#########################################################################

/* email olga@csd.uwo.ca for any questions, suggestions and bug reports

 /*****************    IMPORTANT!!!!!!!!!!!***********************************************************

  If you use this software, YOU HAVE TO REFERENCE (at least) 3 papers, the citations [1]
  [2] and [3] below

/****************************************************************************************************/
/*
0. Matlab Wrapper.
   This README file was written by Olga Veksler and reffers to the C++ core implementation. 
   In order to use the Matlab Wrapper you should
   a. unzip the bundle into a directory within your Matlab's path
   b. compile the required mex-files using
      >> compile_gc
      (You might need to set your mex compiler first. Type mex -setup on Matlab's prompt)
   c. type doc GraphCut and you will have the rest of the necessary documentation.
   
   This software is for academic use ONLY. 
   If you are using this software please note required citations in the Matlab documenation.
   
   For any questions/remarks/problems with the Matlab wrapper please contact shai.bagon@weizmann.ac.il
   
   
1. Introduction.



	This software library implements the Graph Cuts Energy Minimization methods
	described in 
	
	  
		[1] Efficient Approximate Energy Minimization via Graph Cuts 
		    Yuri Boykov, Olga Veksler, Ramin Zabih, 
		    IEEE transactions on PAMI, vol. 20, no. 12, p. 1222-1239, November 2001. 


    
	This software can be used only for research purposes, you should cite
	the aforementioned paper in any resulting publication.
	If you wish to use this software (or the algorithms described in the aforementioned paper)
	for commercial purposes, you should be aware that there is a US patent: 

		R. Zabih, Y. Boykov, O. Veksler, 
		"System and method for fast approximate energy minimization via graph cuts ", 
		United Stated Patent 6,744,923, June 1, 2004



/* Together with the library implemented by O. Veksler, we provide, with the permission of the
    V. Kolmogorov and Y. Boykov the following libraries:  

  
1)	energy.h, which was developed by Vladimir Kolmogorov and  implements binary energy minimization 
	technique described in

	[2] What Energy Functions can be Minimized via Graph Cuts?
	    Vladimir Kolmogorov and Ramin Zabih. 
	    To appear in IEEE Transactions on Pattern Analysis and Machine Intelligence (PAMI). 
	    Earlier version appeared in European Conference on Computer Vision (ECCV), May 2002. 


	We use "energy.h" to implement the binary energy minimization step
	for the alpha-expansion and swap algorithms. The graph construction provided by "energy.h" is
	more efficient (and slightly more general) than the original graph construction for the 
	alpha-expansion algorithm in the paper cited as [1]
	

	This software can be used only for research purposes. IF YOU USE THIS SOFTWARE,
	YOU SHOULD CITE THE AFOREMENTIONED PAPER [2] IN ANY RESULTING PUBLICATION.

	

2) 	graph.h, block.h, maxflow.cpp
	
	This software library implements the maxflow algorithm
	described in

		[3] An Experimental Comparison of Min-Cut/Max-Flow Algorithms
		    for Energy Minimization in Vision.
		    Yuri Boykov and Vladimir Kolmogorov.
		    In IEEE Transactions on Pattern Analysis and Machine Intelligence (PAMI), 
		    September 2004

	This algorithm was developed by Yuri Boykov and Vladimir Kolmogorov
	at Siemens Corporate Research. To make it available for public use,
	it was later reimplemented by Vladimir Kolmogorov based on open publications.

	If you use this software for research purposes, you should cite
	the aforementioned paper in any resulting publication. 
*/

/* These 4 files (energy.h,graph.h, block.h, maxflow.cpp) are included in the curent library with permission of
Vladimir Kolmogorov and Yuri Boykov. They are included in a separate subdirectory named NotVekslerCode.
The can  also be downloaded independently from Vladimir Kolmogorov's
website:http://research.microsoft.com/~vnk/
Please Note that Vladimir's website is likely to move in the future                                         */


Tested under windows, Visual C++ 6.0 compiler 

##################################################################

2. License.

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


##################################################################

3. Energy Minimization

This software is for minimizing energy functions of the form:

E(l) = sum_p D(p,l_p)  + sum_{p,q} Vpq(l_p,l_q)

Here we have a finite set of sites (or pixels) P and a finite set of labels L.
A labeling l is assignments of labels in L to pixels in P. The individual pixels 
are referred to with small letters p and q, label of pixel p is denoted by l_p,
and the set of all label-pixel assignments is denoted by l, that is
l = {l_p | p in P}.

The first term in the energy function E(l) is typically called the data term, and
it consists of the sum over all pixels p of the penalty(or cost) D(p,l_p), what
should be the cost of assigning label l_p to pixel p.  D(p,l_p) can be arbitrary.

The second term is a sum over all pairs of neighboring pixels {p,q}. 
That is there is a neighborhood relation on the set of pixels (this relationship
is symmetric, that is if p is a neighbor of q then q is a neighbor of p).
Here we assume that the neighbor pairs are unordered. This means that if pixels p and q are 
neighbors, then there is either Vpq(l_p,l_q) in the second sum of the energy,
or Vqp(l_q,l_p), but not both. This is not a restriction, since in practice, one can always go
from the ordered energy to the unordered one.  This second term is typically called the smoothness
term.

The expansion algorithm for energy minimization can be used whenever for any 3 labels a,b,c
V(a,a) + V(b,c) <= V(a,c)+V(b,a). In other words, expansion algorithm can be used if
the binary energy for the expansion algorithm step is regular, using V. Kolmogorov's terminology.

The swap algorithm for energy minimization can be used whenever for any 2 labels a,b
V(a,a) + V(b,b) <= V(a,b)+V(b,a). In other words, swap algorithm can be used if
the binary energy for the swap algorithm step is regular, using V. Kolmogorov's terminology.

##################################################################

4. Datatypes

a) EnergyTermType. This is the type for each individual energy term,
that is for the terms D and V.   By default, it  is set to short.  
To change it, go into file "graph.h"  and modify the statement

"typedef int captype;"   from short to any desired type.  


b) EnergyType. This is the type for the total energy (for the sum of all
the D and V terms).    By default, it  is set to int. To change it, go into file "graph.h"  
and change the statement "typedef int flowtype;" to any desired type.  Be very careful to 
avoid overflow if you change this type.
The sum of many terms of type EnergyTermType shouldn't overflow the EnergyType.


c) Label type, is the type to use for the label names. Currently set to integers. In order
to save space, you may want to change it to char or short. Can be also set to long,
but not to float or double.  To change this type, go to "GCoptimization.h"

typedef int LabelType;

d) PixelType: the type to use for pixel names.  Currently set to integers. For
smaller problems, to save space, you may want to change it to  short. Can be also set to long,
but not to float or double.  To change this type, go to "GCoptimization.h"
	
/* Type for pixel. Can be set to short, int, long */ 
typedef int PixelType;



###########################################################################


5. Specifying the energy

Before optimizing the energy, one has to specify it, that is specify the number of
labels, number of pixels, neighborhood system, the data terms, and the smoothness terms.
There are 2 main constructors to use, one in case of the grid graph, and another in case
of a general graph.
In all cases, it is assumed that the pixels are numbered from  
from 0...num_pixels-1, where num_pixels is the number of pixels, and the number of labels,
which are assumed to be numbered from 0....num_labels-1, where num_labels is the number of labels.
For a grid (4-connected) graph, pixel at coordinates (x,y) is numbered with x+y*width, where width
is the width of the grid, that is the row-major ordering of arrays is assumed. 
________________________________________________________________________________________________

Constructor A.

GCoptimization(PixelType width,PixelType height,int num_labels,int dataSetup, int smoothSetup);

Use this constructor only for grid of size width by height.  If you use this constructor, 
4 connected grid neigbhorhood structure is assumed, so you don't need to specify neighborhood
structure separately (and indeed cannot do so). Input parameters dataSetup and smoothSetup are
explained below, in "Section 6. Setting the data and smoothness terms" 
_______________________________________________________________________________________________

Constructor B.

GCoptimization(PixelType num_pixels,int num_labels,int dataSetup, int smoothSetup);   

Use this constructor for general graphs.  If you use this constructor, you must setup up
neighborhood system using function setNeighbors() for each pair of neighboring pixels.
There are 2 types of setNeighbor functions:
 
void setNeighbors(PixelType p, PixelType q, EnergyTermType w_pq);
void setNeighbors(PixelType p, PixelType q);

Coefficient w_pq is used whenever the smoothness term between pixels p and q depends on
the individual pixels p and q, or in other words, is "spacially varying".  For example,
if Vpq(l_p,l_q) = penalty(l_p,l_q)*w_pq, where penalty(l_p,l_q) is some function that
depends only on the labels l_p,l_q, then setNeighbors(p,q,w_pq) should be called.  
If w_pq = 1 for all neighbor pixels p and q, than you can call setNeighbors(p,q)
(calling  setNeighbors(p,q,1) achieves the same thing).
Note that this function setNeighbor has to be called exactly one time for each neighbor pair.  
That is if pixels p and q are neighbors, you can call either setNeighbors(p,q) or setNeighbors(q,p)
BUT NOT BOTH. 

 Input parameters dataSetup and smoothSetup are explained below in "Section 6 Setting the data and smoothness terms" 
_______________________________________________________________________________________________

Constructor C. 

GCoptimization(LabelType *m_answer,PixelType num_pixels,int nLabels,int dataSetup, int smoothSetup);

This constructor is exactly the same as constructor A, but in addition, pointer to the array where
the final labels should be stored is passed, namely m_answer.  m_answer should point to the
array of size num_pixels (which is width*height for the grid graph).  This is done to save space,
if needed, so that the as the answer will not have to be stored twice, once in the current class, 
and once in the class which calls this optimization.

_______________________________________________________________________________________________

Constructor D.

GCoptimization(LabelType *m_answer,PixelType width,PixelType height,int num_labels,int dataSetup, int smoothSetup);

This constructor is exactly the same as constructor B, but in addition, pointer to the array where
the final labels should be stored is passed, namely m_answer.  m_answer should point to the
array of size num_pixels (which is width*height for the grid graph).  This is done to save space,
if needed, so that the as the answer will not have to be stored twice, once in the current class, 
and once in the class which calls this optimization.

_______________________________________________________________________________________________


6. Setting the data and smoothness terms.

The way the data and smoothness terms are setup is controlled by the input  parameters 
to the constructor (these parameters are common to all constructors), namely 
 parameters dataSetup and smoothSetup. These parameters can take only 2 values, namely SET_INDIVIDUALLY (0) and   
SET_ALL_AT_ONCE(1).  

------------------------dataSetup-----------------------
In case dataSetup = SET_INDIVIDUALLY, to set the data cost you must use the            
member function setDataCost(pixel,label,cost), for each pixel and label combination. That is each
data term is set up individually.  This function sets D_pixel (label) = cost.
If dataSetup = SET_ALL_AT_ONCE,  to set the data costs you must use one of the three setData() functions,
either by passing an array of data costs (of appropriate size), or a pointer to a function which 
returns data cost term. More details on different setData() functions:               
         
(a) void setData(EnergyTermType *DataCost);
	DataCost is an array s.t. the data cost for pixel p and  label l is stored at                        
	DataCost[pixel*num_labels+l].  If the current neighborhood system is a grid, then                    
        the data term for label l and pixel with coordinates (x,y) is stored at                               
	DataCost[(x+y*width)*num_labels + l]. Thus the size of array DataCost is num_pixels*num_labels 

(b) void setData(dataFnPix dataFn); 
	dataFn is a pointer to a function  f(Pixel p, Label l), s.t. the data cost for pixel p to have      
	label l  is given by f(p,l) 

(c)  void setData(dataFnCoord dataFn);
        This function  can be used only for a grid graph. dataFn is a pointer to a function  
        f(x, y, l), s.t. the data cost for pixel with coordinates (x,y) to have  label l  
        is given by f(x,y,l) 
	
Note that only one of the above setData() functions can be used.    

------------------------dataSetup-----------------------
In case smoothSetup = SET_INDIVIDUALLY, to set the smooth cost you must use the member function 
setSmoothCost(label1,label2,cost).  This function sets V(label1,label2) = cost. Notice that
no spatially varying coefficient w_pq is allowed in this case.
If smoothSetup = SET_ALL_AT_ONCE,  to set the smoothness costs you must use any of the setSmoothness() 
functions, either by passing an array of smoothness costs, or a pointer to a function which returns 
smoothness cost. More details on different setSmoothness() functions:

(a) void setSmoothness(EnergyTermType* V);
         V is an array of smoothness costs, such that V_pq(label1,label2)  is stored at V[label1+num_labels*label2]        
	 If graph is a grid, then using this  function only if the smooth costs are not spacially varying    
	 that is the smoothness penalty V depends only on labels, but not on pixels.  If the graph is 
         not a grid, then you can specify spacially varying coefficients w_pq when you set up the
         neighborhood system using setNeighbor(p,q,w_pq) function. In this case, 
         V_pq(label1,label2) =  V[label1+num_labels*label2]*w_pq                            
	 
(b) void setSmoothness(EnergyTermType* V,EnergyTermType* hCue, EnergyTermType* vCue);
	 This function should be used only if the graph is a grid. Array V is the same as above, under (a).
         Arrays hCue and vCue have the same size as the image (that is width*height), and are used to set
         the spatially varying coefficients w_pq. If p = (x,y) and q = (x+1,y), then 
         w_pq =  hCue[x+y*width], and so the smoothness penalty for pixels (x,y) and (x+1,y) to have labels       
	 label1 and label2, that is V_pq(label1,label2) = V[label1+num_labels*label2]*hCue[x+y*width]
         If p = (x,y) and q = (x,y+q), then 
         w_pq =  vCue[x+y*width], and so the smoothness penalty for pixels (x,y) and (x,y+1) to have labels       
	  label1 and label2, that is V_pq(label1,label2) = V[label1+num_labels*label2]*vCue[x+y*width]

(c) void setSmoothness(smoothFnCoord cost);

          cost is pointer to a function f(pix1,pix2,label1,label2) such that smoothness penalty for neigboring pixels     
	  pix1 and pix2 to  have labels, respectively, label1 and label2 is f(pix1,pix2,label1,label2)         

(d)  void setSmoothness(smoothFnCoord horz_cost, smoothFnCoord vert_cost);
	 
	This function  can be used only if the graph is a grid.                                              
        horz_cost is a poineter to a function f(x,y,label1,label2) such that smoothness penalty for neigboring pixels      
	(x,y) and (x+1,y) to have labels, respectively, label1 and label2 is f(x,y,label1,label2)            
        vert_cost is a pointer to a function f(x,y,label1,label2) such that smoothness penalty for neigboring pixels      
	 /* (x,y) and (x,y+1) to have labels, respectively, label1 and label2 is f(x,y,label1,label2)            
	

Note that only one of the above setSmoothness() functions can be used.    


##################################################################

6. Optimizing the energy

You can optimize the energy and get the resulting labeling using the following functions.  Notice that they can 
be called as many times as one wishes after the constructor has been called and the data/smoothness terms
(and the neighborhood system, if general graph) has beeen set.  The initial labeling is set to consists of
all 0's. Use function setLabel(PixelType pixelP, LabelType labelL), described under heading (x) in this section
to initialize the labeling to anything else (but in the valid range, of course, labels must be between
0 and num_labels-1)


i) expansion(int max_num_iterations)
Will run the expansion algorithm up to the specified number of iterations.
Returns the energy of the resulting labeling.

ii)expansion();
Will run the expansion algorithm to convergence (convergence is guaranteed)
Returns the energy of the resulting labeling
	
iii) oneExpansionIteration();
 Performs one iteration (one pass over all labels)  of expansion algorithm, see the paper for more details.
 Returns the energy of the resulting labeling


iv)  alpha_expansion(LabelType alpha_label);
Performs  expansion on the label specified by alpha_label.  Returns the energy of the resulting labeling
	
v)	swap(int max_num_iterations);
Will run the swap algorithm up to the specified number of iterations.
Returns the energy of the resulting labeling.


vi)  swap();
Will run the swap algorithm up to convergence (convergence is guaranteed)
Returns the energy of the resulting labeling
	

vii) oneSwapIteration();
Performs one iteration (one pass over all pairs of labels)  of the swap algorithm, see the paper for more details.
Returns the energy of the resulting labeling.

	
viii) alpha_beta_swap(LabelType alpha_label, LabelType beta_label);
Performs  swap on a pair of labels, specified by the input parameters alpha_label, beta_label.
Returns the energy of the resulting labeling.


ix)	whatLabel(PixelType pixelP)
Returns the current label assigned to pixelP.  Can be called at any time after the constructor call.

x) setLabel(PixelType pixelP, LabelType labelL)
Sets the label of pixelP to the the input parameter labelL. Can be called at any time after the constructor call.
This function is useful, in particular, to  initialize the labeling to something specific before optimization starts.

xi) setLabelOrder(bool RANDOM_LABEL_ORDER)
By default, the labels for the swap and expansion algorithms are visited in random order, thus the results
are going to be slightly different each time the optimization is invoked. To set the label order to
be not random, call setLabelOrder(0).  To set it to be random again, call setLabelOrder(1). Notice,
that by using functions under heading (iv) and (viii) you can completely  and exactly specify the desired
order on labels.

xii) EnergyType giveDataEnergy();
Returns the data part of the energy of the current labling

	
xiii)	EnergyType giveSmoothEnergy();
Returns the smoothness part of the energy of the current labling

##################################################################

7. Example usage.

Example 1, uses constructor A.

__________________________________________________________________

#include <stdio.h>
#include <time.h>
#include "GCoptimization.h"

void main(int argc, char **argv)
{

	GCoptimization *optimize = (GCoptimization *) new GCoptimization(3,2, SET_INDIVIDUALLY, SET_INDIVIDUALLY);
	GCoptimization::EnergyType engS,engD,engT;

	// First set the data costs terms for each pixel and each label
	optimize ->setDataCost(0,0,5);
	optimize ->setDataCost(0,1,1);
	optimize ->setDataCost(1,0,3);
	optimize ->setDataCost(1,1,0);
	optimize ->setDataCost(2,0,-3);
	optimize ->setDataCost(2,1,3);


	//Next set the neighboring pixels
	optimize->setNeighbors(0,1,7);

	optimize->setNeighbors(1,2,5);

	//Finally, specify the remaining part of Vpq.  This is the part that
	// depends just on labels, not on  pixels, and in this case 
	// it is penalty(label1,label2) = |label1-label2|

	optimize->setSmoothCost(0,0,0);
	optimize->setSmoothCost(0,1,1);
	optimize->setSmoothCost(1,0,1);
	optimize->setSmoothCost(1,1,0);

	////////////////////////////////////////////////////////////////////////
	/* Now the energy is completely specified. Can call any optimization  */
	/* methods */

	engD = optimize->giveDataEnergy();
	engS = optimize->giveSmoothEnergy();

	printf("\nBefore optimization, the smooth energy is %d, data energy %d, total %d",engS,engD,engS+engD);

	engT = optimize->expansion(); //to run expansion algorithm to convergence
	//eng = optimize->swap();      //to run swap algorithm to convergence

	engD = optimize->giveDataEnergy();
	engS = optimize->giveSmoothEnergy();

	printf("\nAfter optimization, the smooth energy is %d, data energy %d, total %d",engS,engD,engS+engD);
	for( int i = 0; i < 3; i++ )
		printf("\nPixel %d has label %d",i,optimize->whatLabel(i));
	

}

__________________________________________________________________

Example 2, uses constructor A


#include <stdio.h>
#include <time.h>
#include "GCoptimization.h"


// Suppose we have a grid of width 3 and height 2. That is there are 6 pixels
// Suppose there are 7 labels.
// The neighborhood structure is the usual grid, so we will use constructor C
// Let the data costs be: 
// D(pixel,label) = 0  if pixel < 3 and label = 1
//                = 10 if pixel < 3 and label is not equal to 1
//                = 0  if pixel >= 3 and label = 6
//                = 10 if pixel >= 3 and label is not equal to 6

// Let the smoothness terms be the so called "Potts model",
// that is Vpq(l_p,l_q) = w_pq  if |l_p-l_q| > 1
//                      = 0     if l_p = l_q
// and let w_pq be as pictured:
//
//
//           o   __2__    o  __10__  o
//         
//           |            |          | 
//           3            1          5
//           |            |          | 
//           o   __8__    o  __4__   o
  

/****************************************************************************/

void main(int argc, char **argv)
{
	
	int num_pixels = 6, num_labels = 7, width = 3, height = 2;
	GCoptimization::EnergyTermType *datacost,*smoothcost,*vertWeights,*horizWeights;
	GCoptimization::EnergyType engS,engD,engT;

        /* First call the constructor for a grid graph */
	GCoptimization *optimize = (GCoptimization *) new GCoptimization(width,height,num_labels,SET_ALL_AT_ONCE,SET_ALL_AT_ONCE);
	
	datacost     = (GCoptimization::EnergyTermType *) new GCoptimization::EnergyTermType[num_pixels*num_labels];
	smoothcost   = (GCoptimization::EnergyTermType *) new GCoptimization::EnergyTermType[num_labels*num_labels];
	vertWeights  = (GCoptimization::EnergyTermType *) new GCoptimization::EnergyTermType[num_pixels];
	horizWeights = (GCoptimization::EnergyTermType *) new GCoptimization::EnergyTermType[num_pixels];
	
	// Fill in the datacost matrix with the correct values
	for ( int pix = 0; pix < num_pixels; pix++ )
		for ( int l = 0; l < num_labels; l++ )
		{
			if ( pix < 3 && l == 1)
				datacost[pix*num_labels+l] = 0;
			else if ( pix < 3 && l != 1)
				datacost[pix*num_labels+l] = 10;
			else if ( pix >= 3 && l == 6 )
				datacost[pix*num_labels+l] = 0;
			else datacost[pix*num_labels+l] = 10;
	

		}


	// Fill in the smoothcost matrix with the correct values
	for ( int i = 0; i < num_labels; i++ )
		for ( int j = 0; j < num_labels; j++ )
			if ( i != j )
				smoothcost[i+j*num_labels] = 1;
			else smoothcost[i+j*num_labels] = 0;
		

	// Fill in the horizontal and vertical matrices with the correct values

	vertWeights[0] =  3;
	vertWeights[1] =  1;
	vertWeights[2] =  5;

	horizWeights[0] = 2;
	horizWeights[1] = 10;
	horizWeights[3] = 8;
	horizWeights[4] = 4;

        optimize->setData(datacost);
	optimize->setSmoothness(smoothcost,horizWeights,vertWeights);

	///////////////////////////////////////////////////////////////////////
	/* Now the energy is completely specified. Can call any optimization  */
	/* methods */

	srand(time(NULL));
	//	Just for fun, start with random labeling
	for ( i = 0; i < num_pixels; i++ ) 
		optimize->setLabel(i,rand()%num_labels);



	engD = optimize->giveDataEnergy();
	engS = optimize->giveSmoothEnergy();

	printf("\nBefore optimization, the smooth energy is %d, data energy %d, total %d",engS,engD,engS+engD);

	engT = optimize->alpha_beta_swap(1,0);      //run swap algorithm on labels 1 and 0
	engD = optimize->giveDataEnergy();
	engS = optimize->giveSmoothEnergy();


	printf("\nAfter swapping labels 0 and 1, the smooth energy is %d, data energy %d, total %d",engS,engD,engS+engD);

	engT = optimize->expansion(); //run expansion algorithm to convergence

	engD = optimize->giveDataEnergy();
	engS = optimize->giveSmoothEnergy();

	printf("\nAfter optimization, the smooth energy is %d, data energy %d, total %d",engS,engD,engS+engD);
	for(  i = 0; i < num_pixels; i++ )
		printf("\nPixel %d has label %d",i,optimize->whatLabel(i));

}

__________________________________________________________________
