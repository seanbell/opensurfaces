
#include "mex.h"
#include "GCoptimization.h"
#include "GraphCut.h"
#include <stdlib.h>
#include <math.h>

/* Defines */
// define A64BITS for compiling on a 64 bits machine...

/*
 * Matlab wrapper for Weksler graph cut implementation
 *
 * usage:
 * [gch] = GraphCut3dConstr(R, C, Z, num_labels, DataCost, SmoothnessCost, [Contrast])
 *
 * Note that data types are crucials!
 * 
 * Inputs:
 *  R, C, Z - size of 3D grid. 
 *  num_labels - number of labels.  
 *  DataCost - of type float, array size [width*height*depth*#labels], the data term for pixel
 *             x,y,z recieving label l is stroed at [(x+y*width+z*width*depth)*#labels + l]
 *  SmoothnessCost - of type float, array size [#labels.^2] the cost between l1 and l2 is
 *                   stored at [l1+l2*#labels] = Vpq(lp,lq)
 *  Contrast - of type float, array size[width*height*depth], the weight Wpq will be determined by the contrast:
 *                  Wpq = exp(-|C(p)-C(q)|)
 *
 * Outputs:
 *  gch - of type int32, graph cut handle - do NOT mess with it!
 */
void mexFunction(
    int		  nlhs, 	/* number of expected outputs */
    mxArray	  *plhs[],	/* mxArray output pointer array */
    int		  nrhs, 	/* number of inputs */
    const mxArray	  *prhs[]	/* mxArray input pointer array */
    )
{
    
    int num_labels;
    Graph::captype *DataCost;
    Graph::captype *SmoothnessCost;
    Graph::captype *Contrast = NULL;
    GCoptimization::LabelType *Labels;
    GCoptimization::PixelType R, C, Z; 
    
    GCoptimization *MyGraph = NULL;
        
    /* check number of inout arguments - must be 6 */
    if ((nrhs != 6)&&(nrhs!=7)) {
        mexErrMsgIdAndTxt("GraphCut:NarginError","Wrong number of input argumnets");
    }
    GetScalar(prhs[0], R);
    GetScalar(prhs[1], C);
    GetScalar(prhs[2], Z);
    GetScalar(prhs[3], num_labels);
    
  
    /* check second input DataCost: must have #labels*height*width elements of type float */
    if ( mxGetNumberOfElements(prhs[4]) != num_labels*R*C*Z ) {
        mexErrMsgIdAndTxt("GraphCut:DataCost",
        "DataCost argument does not contains the right number of elements");
    }
    if (mxGetClassID(prhs[4]) != mxSINGLE_CLASS ) {
        mexErrMsgIdAndTxt("GraphCut:DataCost",
        "DataCost argument is not of type float");
    }
    DataCost = (Graph::captype*)mxGetData(prhs[4]);

    /* check fifth input SmoothnessCost: must have #labels.^2 elements of type float */
    if ( mxGetNumberOfElements(prhs[5]) != num_labels*num_labels ) {
        mexErrMsgIdAndTxt("GraphCut:SmoothnessCost",
        "SmoothnessCost argument does not contains the right number of elements");
    }
    if (mxGetClassID(prhs[5]) != mxSINGLE_CLASS ) {
        mexErrMsgIdAndTxt("GraphCut:SmoothnessCost",
        "SmoothnessCost argument is not of type float");
    }
    SmoothnessCost = (Graph::captype*)mxGetData(prhs[5]);

    if ( nrhs == 7 ) { 
        /* add Contrast cue */
        if ( mxGetNumberOfElements(prhs[6]) != R*C*Z ) {
            mexErrMsgIdAndTxt("GraphCut:SmoothnessCost",
            "Contrast argument does not contains the right number of elements");
        }
        if (mxGetClassID(prhs[6]) != mxSINGLE_CLASS ) {
            mexErrMsgIdAndTxt("GraphCut:SmoothnessCost",
            "Contrast argument is not of type float");
        }
        Contrast = (Graph::captype*)mxGetData(prhs[6]);
        
    }
    /* prepare the output argument */
    if ( nlhs != 1 ) {
        mexErrMsgIdAndTxt("GraphCut:OutputArg","Wrong number of output arguments");
    }
    
    MyGraph = new GCoptimization(R*C*Z, num_labels, SET_ALL_AT_ONCE, SET_ALL_AT_ONCE);
    /* neighborhod setup */
    GCoptimization::PixelType c(0), r(0), z(0), p(0), q(0);
    if (Contrast) {
        for ( r = 0 ; r <= R - 2;  r++ ) {
            for ( c = 0 ; c <= C - 2; c++ ) {
                for ( z = 0 ; z <= Z - 2; z++ ) {
                    /* all nodes with 3 nieghbors */
                    p = r+c*R+z*R*C;
                    q = r+1+c*R+z*R*C;
                    MyGraph->setNeighbors(p, q, exp(-fabs(Contrast[p]-Contrast[q])));
                    q = r+(c+1)*R+z*R*C;
                    MyGraph->setNeighbors(p, q, exp(-fabs(Contrast[p]-Contrast[q])));
                    q = r+c*R+(z+1)*R*C;
                    MyGraph->setNeighbors(p, q, exp(-fabs(Contrast[p]-Contrast[q])));
                }
               /* top of Z has 2 n in c and r */
                p = r+c*R+z*R*C;
                q = r+1+c*R+z*R*C;
                MyGraph->setNeighbors(p, q, exp(-fabs(Contrast[p]-Contrast[q])));
                q = r+(c+1)*R+z*R*C;
                MyGraph->setNeighbors(p, q, exp(-fabs(Contrast[p]-Contrast[q])));
            }
            /* end of c has 2 n in z and r */
            for ( z = 0 ; z <= Z -2 ; z++ ) {
                p = r+c*R+z*R*C;
                q = r+1+c*R+z*R*C;
                MyGraph->setNeighbors(p, q, exp(-fabs(Contrast[p]-Contrast[q])));
                q = r+c*R+(z+1)*R*C;
                MyGraph->setNeighbors(p, q, exp(-fabs(Contrast[p]-Contrast[q])));
            }
            /* end of c abd z has n in r */
            p = r+c*R+z*R*C;
            q = r+1+c*R+z*R*C;
            MyGraph->setNeighbors(p, q, exp(-fabs(Contrast[p]-Contrast[q])));
        }
        /* end of r has n in z and c */
        for ( c = 0 ; c <= C - 2; c++ ) {
            for ( z = 0 ; z <= Z - 2; z++ ) {
                p = r+c*R+z*R*C;
                q = r+c*R+(z+1)*R*C;
                MyGraph->setNeighbors(p, q, exp(-fabs(Contrast[p]-Contrast[q])));
                q = r+(c+1)*R+z*R*C;
                MyGraph->setNeighbors(p, q, exp(-fabs(Contrast[p]-Contrast[q])));
            }
            p = r+c*R+z*R*C;
            q = r+(c+1)*R+z*R*C;
            MyGraph->setNeighbors(p, q, exp(-fabs(Contrast[p]-Contrast[q])));
        }
        for ( z = 0 ; z <= Z - 2; z++ ) {
            p = r+c*R+z*R*C;
            q = r+c*R+(z+1)*R*C;
            MyGraph->setNeighbors(p, q, exp(-fabs(Contrast[p]-Contrast[q])));
        }
        /* end of graph construction with contrast */
    } else {
        for ( r = 0 ; r <= R - 2;  r++ ) {
            for ( c = 0 ; c <= C - 2; c++ ) {
                for ( z = 0 ; z <= Z - 2; z++ ) {
                /* all nodes with 3 nieghbors */
                    MyGraph->setNeighbors(r+c*R+z*R*C,r+1+c*R+z*R*C);
                    MyGraph->setNeighbors(r+c*R+z*R*C,r+(c+1)*R+z*R*C);
                    MyGraph->setNeighbors(r+c*R+z*R*C,r+c*R+(z+1)*R*C);
                }
            /* top of Z has 2 n in c and r */
                MyGraph->setNeighbors(r+c*R+z*R*C,r+1+c*R+z*R*C);
                MyGraph->setNeighbors(r+c*R+z*R*C,r+(c+1)*R+z*R*C);
            }
        /* end of c has 2 n in z and r */
            for ( z = 0 ; z <= Z -2 ; z++ ) {
                MyGraph->setNeighbors(r+c*R+z*R*C,r+1+c*R+z*R*C);
                MyGraph->setNeighbors(r+c*R+z*R*C,r+c*R+(z+1)*R*C);
            }
        /* end of c abd z has n in r */
            MyGraph->setNeighbors(r+c*R+z*R*C,r+1+c*R+z*R*C);
        }
    /* end of r has n in z and c */
        for ( c = 0 ; c <= C - 2; c++ ) {
            for ( z = 0 ; z <= Z - 2; z++ ) {
                MyGraph->setNeighbors(r+c*R+z*R*C,r+c*R+(z+1)*R*C);
                MyGraph->setNeighbors(r+c*R+z*R*C,r+(c+1)*R+z*R*C);
            }
            MyGraph->setNeighbors(r+c*R+z*R*C,r+(c+1)*R+z*R*C);
        }
        for ( z = 0 ; z <= Z - 2; z++ ) {
            MyGraph->setNeighbors(r+c*R+z*R*C,r+c*R+(z+1)*R*C);
        }
    }
    MyGraph->setData(DataCost);
/*    if ( vCue != NULL && vCue != NULL ) 
        MyGraph->setSmoothness(SmoothnessCost, hCue, vCue);
    else*/
    MyGraph->setSmoothness(SmoothnessCost);
    
        
    /* create a container for the pointer */
    int dims[2] = {1,0};
    plhs[0] = mxCreateNumericArray(1, dims, MATLAB_POINTER_TYPE, mxREAL);
    
    GraphHandle* gh;
    gh = (GraphHandle*) mxGetData(plhs[0]);
    *gh = (GraphHandle)(MyGraph);
}
    

