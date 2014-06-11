#include "mex.h"
#include <memory.h>
#include "mpi_kmeans.h"

void mexFunction(const int nlhs, mxArray *plhs[], const int nrhs, const mxArray *prhs[])
{

#ifdef COMPILE_WITH_ICC
	unsigned int dims[2];
#else
	mwSize dims[2];
#endif

	unsigned int dim = mxGetM(prhs[0]);
	unsigned int npts = mxGetN(prhs[0]);
	unsigned int nclus = mxGetN(prhs[1]);

	if (mxGetM(prhs[1])!=dim)
		mexErrMsgTxt("Dimension mismatch in input arguments");

	dims[0]= npts;
	dims[1] = 1;
	plhs[0] = mxCreateNumericArray(2,dims,mxUINT32_CLASS,mxREAL);
	unsigned int *c = (unsigned int*)mxGetPr(plhs[0]);

	/* input points */
	const PREC *X = (PREC*)mxGetPr(prhs[0]);

	/* cluster centers */
	const PREC *CX = (PREC*)mxGetPr(prhs[1]);
	
	const PREC *px=X;

	/* sanity check */
	for (unsigned int i=0 ; i<npts*dim; i++)
		if (mxIsNaN(px[i])||mxIsInf(px[i]))
			mexErrMsgTxt("NaN or Inf in the input data detected... abort");


	for (unsigned int i=0 ; i<npts; i++,px+=dim)
		c[i] = 1+assign_point_to_cluster_ordinary(px, CX, dim, nclus);

}




