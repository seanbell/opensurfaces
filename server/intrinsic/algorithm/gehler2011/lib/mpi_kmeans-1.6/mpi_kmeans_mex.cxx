#include <memory.h>
#include "mex.h"
#include "mpi_kmeans.h"
#include <assert.h>

void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[])
{

#ifdef COMPILE_WITH_ICC
	unsigned int dims[2];
#else
	mwSize dims[2];
#endif

	if (nrhs < 2){
		mexPrintf("at least two input arguments expected.");
		return;
	}
	unsigned int maxiter = 0;
	if (nrhs > 2)
		maxiter = (unsigned int) *(mxGetPr(prhs[2]));
	
	unsigned int restarts = 0;
	if (nrhs > 3)
		restarts = (unsigned int) *(mxGetPr(prhs[3]));

	const PREC *W = NULL;
	/* weighting */
	if (nrhs > 4)
		W = (PREC*)mxGetPr(prhs[4]);



#if KMEANS_VERBOSE>0
	if (restarts>0)
		printf("will do %d restarts\n",restarts);
#endif

	if ((nlhs > 3) || (nlhs < 1)){
		mexPrintf("minimal one, maximal three output arguments expected.");
		return;
	}

#ifdef INPUT_TYPE
#if INPUT_TYPE==0
	if (!mxIsDouble(prhs[0]) || mxIsComplex(prhs[0]) ||
		mxGetNumberOfDimensions(prhs[0]) != 2)
	{
		mexPrintf("input 1 (X) must be a real double matrix");
		return;
	}
#elif INPUT_TYPE==1
	if (!mxIsSingle(prhs[0]) || mxIsComplex(prhs[0]) ||
		mxGetNumberOfDimensions(prhs[0]) != 2)
	{
		mexPrintf("input 1 (X) must be a real single matrix");
		return;
	}
#endif
#endif

	unsigned int dim = mxGetM(prhs[0]);
	unsigned int npts = mxGetN(prhs[0]);

	unsigned int nclus = 0;
	if (mxGetN(prhs[1])==1 && mxGetM(prhs[1])==1)
		nclus = (unsigned int)*(mxGetPr(prhs[1]));
	else
	{
		nclus = mxGetN(prhs[1]);
		if (dim != mxGetM(prhs[1]))
			mexErrMsgTxt("Dimension mismatch");
	}
	if (nclus == 0)
		mexErrMsgTxt("Number of Clusters is zero");

	if (npts < nclus)
		mexErrMsgTxt("less training points than clusters to compute");

/*	if (mxIsSingle(prhs[1]))
	printf("Is Single!\n");
*/

	if (mxIsComplex(prhs[1]) ||
		mxGetNumberOfDimensions(prhs[1]) != 2)
	{
		mexPrintf("input 2 (CX) must be a real double matrix compatible with input 1 (X)");
		return;
	}

	if (nrhs>4)
	{
		if (mxGetM(prhs[4]) != npts)
			mexErrMsgTxt("Dimension mismatch weights to points");
		if (mxGetN(prhs[4]) != 1)
			mexErrMsgTxt("Dimension mismatch weights should be npoints x 1");
	}

	dims[0] = dim;
	dims[1] = nclus;

#ifdef INPUT_TYPE
#if INPUT_TYPE==0
	//plhs[0] = mxCreateDoubleMatrix(dim, nclus, mxREAL);
	plhs[0] = mxCreateNumericArray(2, dims, mxDOUBLE_CLASS, mxREAL);
#elif INPUT_TYPE==2


	plhs[0] = mxCreateNumericArray(2, dims, mxSINGLE_CLASS, mxREAL);
#endif
#endif

	PREC *CXp = (PREC*)mxGetPr(plhs[0]);

	/* input points */
	const PREC *X = (PREC*)mxGetPr(prhs[0]);


	/* sanity check */
	for (unsigned int i=0 ; i<npts*dim; i++)
		if (mxIsNaN(X[i])||mxIsInf(X[i]))
			mexErrMsgTxt("NaN or Inf in the input data detected... abort");

	/* return also the assignment */
	unsigned int *assignment = NULL;
	if (nlhs>2) 
	{
		dims[0] = npts;
		dims[1] = 1;
		plhs[2] = mxCreateNumericArray(2,dims,mxUINT32_CLASS,mxREAL);
		assignment = (unsigned int*)mxGetPr(plhs[2]);
	}
	else
		assignment = (unsigned int *) malloc(npts * sizeof(unsigned int)); 	/* assignement of points to cluster */

	assert(assignment);

	if ((mxGetN(prhs[1])==mxGetM(prhs[1]))!=1)
	{
		/* copy initial guess to CXp (otherwise use kmeans start assignment) */
		memcpy(CXp,mxGetPr(prhs[1]),dim*nclus*sizeof(PREC));
	}

	/* start kmeans */
	PREC sse = kmeans(CXp,X,W,assignment,dim,npts,nclus,maxiter,restarts);

	if (nlhs>1)
	{
		plhs[1] = mxCreateScalarDouble(0.0);
		PREC *psse = (PREC*)mxGetPr(plhs[1]);
		psse[0] = sse;
	}

	/* return also the assignment */
	if (nlhs>2)
	{
		for ( unsigned int i=0; i<npts; i++)
			assignment[i]++;
	}
	else
		free(assignment);
}




