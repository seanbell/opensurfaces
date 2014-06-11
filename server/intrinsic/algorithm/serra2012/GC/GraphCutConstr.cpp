
#include "mex.h"
#include "GCoptimization.h"
#include "GraphCut.h"
#include <stdlib.h>

/* Defines */


/*
 * Matlab wrapper for Weksler graph cut implementation
 *
 * usage:
 * [gch] = GraphCutConstr(width, height, num_labels, DataCost, SmoothnessCost,[vCost,hCost])
 *
 * Note that data types are crucials!
 * 
 * Inputs:
 *  width, hieght - 2D grid dimensions. (do not cast to int)
 *  num_labels - number of labels.  (do not cast to int)
 *  DataCost - of type float, array size [width*height*#labels], the data term for pixel
 *             x,y recieving label l is stroed at [(x+y*width)*#labels + l]
 *  SmoothnessCost - of type float, array size [#labels.^2] the cost between l1 and l2 is
 *                   stored at [l1+l2*#labels] = Vpq(lp,lq)
 *  vCost, hCost - of type float, array size[width*height] each, 
 *                 horizontal and vertical cues for smoothness term
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
    
    GCoptimization::PixelType width, height;
    int num_labels;
    Graph::captype *DataCost;
    Graph::captype *SmoothnessCost;
    Graph::captype *hCue = NULL;
    Graph::captype *vCue = NULL;
    GCoptimization::LabelType *Labels;
    int dims[2]; /* for labels allocation */
    
    GCoptimization *MyGraph = NULL;
        
       /* check number of inout arguments - must be 5 */
    if ((nrhs != 5)&&(nrhs!=7)) {
        mexErrMsgIdAndTxt("GraphCut:NarginError","Wrong number of input argumnets");
    }
    
    /* check first input width: must be 1 int element */
    GetScalar(prhs[0], width);
    dims[1] = width;
    
    /* check second input height: must be 1 element */
    GetScalar(prhs[1], height);
    dims[0] = height;
    
    /* check third input #labels: must be single element */
    GetScalar(prhs[2], num_labels);
    
    /* check fourth input DataCost: must have #labels*height*width elements of type float */
    if ( mxGetNumberOfElements(prhs[3]) != num_labels*width*height ) {
        mexErrMsgIdAndTxt("GraphCut:DataCost",
        "DataCost argument does not contains the right number of elements");
    }
    if (mxGetClassID(prhs[3]) != mxSINGLE_CLASS ) {
        mexErrMsgIdAndTxt("GraphCut:DataCost",
        "DataCost argument is not of type float");
    }
    DataCost = (Graph::captype*)mxGetData(prhs[3]);

    /* check fifth input SmoothnessCost: must have #labels.^2 elements of type float */
    if ( mxGetNumberOfElements(prhs[4]) != num_labels*num_labels ) {
        mexErrMsgIdAndTxt("GraphCut:SmoothnessCost",
        "SmoothnessCost argument does not contains the right number of elements");
    }
    if (mxGetClassID(prhs[4]) != mxSINGLE_CLASS ) {
        mexErrMsgIdAndTxt("GraphCut:SmoothnessCost",
        "SmoothnessCost argument is not of type float");
    }
    SmoothnessCost = (Graph::captype*)mxGetData(prhs[4]);
    
    if ( nrhs == 7 ) {
        /* add hCue and vCue */
        if ( mxGetNumberOfElements(prhs[5]) != width*height ) {
            mexErrMsgIdAndTxt("GraphCut:SmoothnessCost",
            "vCue argument does not contains the right number of elements");
        }
        if (mxGetClassID(prhs[5]) != mxSINGLE_CLASS ) {
            mexErrMsgIdAndTxt("GraphCut:SmoothnessCost",
            "vCue argument is not of type float");
        }
        vCue = (Graph::captype*)mxGetData(prhs[5]);
        
        if ( mxGetNumberOfElements(prhs[6]) != width*height ) {
            mexErrMsgIdAndTxt("GraphCut:SmoothnessCost",
            "hCue argument does not contains the right number of elements");
        }
        if (mxGetClassID(prhs[6]) != mxSINGLE_CLASS ) {
            mexErrMsgIdAndTxt("GraphCut:SmoothnessCost",
            "hCue argument is not of type float");
        }
        hCue = (Graph::captype*)mxGetData(prhs[6]);
    }
    
    /* prepare the output argument */
    if ( nlhs != 1 ) {
        mexErrMsgIdAndTxt("GraphCut:OutputArg","Wrong number of output arguments");
    }
    
    MyGraph = new GCoptimization(width, height, num_labels, SET_ALL_AT_ONCE, SET_ALL_AT_ONCE);
    MyGraph->setData(DataCost);
    if ( vCue != NULL && vCue != NULL ) 
        MyGraph->setSmoothness(SmoothnessCost, hCue, vCue);
    else
        MyGraph->setSmoothness(SmoothnessCost);
    
        
    /* create a container for the pointer */
    dims[0] = 1; dims[1] = 0;
    plhs[0] = mxCreateNumericArray(1, dims, MATLAB_POINTER_TYPE, mxREAL);
    
    GraphHandle* gh;
    gh = (GraphHandle*) mxGetData(plhs[0]);
    *gh = (GraphHandle)(MyGraph);
}
    

