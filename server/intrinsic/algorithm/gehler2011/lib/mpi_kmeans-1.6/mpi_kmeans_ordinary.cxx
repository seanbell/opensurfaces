#include "mex.h"
#include <float.h>
#include <memory.h>
#include <math.h>
#include <assert.h>
 

// comment for more speed but no sse output
//#define KMEANS_DEBUG
// if you do not want to have any messages printed, comment out the following line
//#define KMEANS_VERBOSE


double compute_distance(const double *vec1, const double *vec2, const unsigned int dim)
{
	double d = 0.0;
	for ( unsigned int k=0 ; k<dim ; k++ )
	{
		double df = (vec1[k]-vec2[k]);
		d += df*df;
	}
	d = sqrt(d);

	return d;
}

double compute_sserror(const double *CX, const double *X, const unsigned int *c,unsigned int dim, unsigned int npts)
{
	const double *px = X;
	double sse = 0.0;
	for ( unsigned int i=0 ; i<npts ; i++,px+=dim)
	{
		const double *pcx = CX+c[i]*dim;
		double d = (double)(compute_distance(px,pcx,dim));
		sse += d*d;
	}
	return(sse);
}

unsigned int assign_point_to_cluster(const double *px, const double *CX, unsigned int dim,unsigned int nclus, double *dist)
{
	const double *pcx = CX;
	unsigned int assignment = nclus;
	double mindist = DBL_MAX;
	for ( unsigned int j=0 ; j<nclus ; j++,pcx+=dim )
	{
		double d = compute_distance(px,pcx,dim);

		if (d<mindist)
		{
			mindist = d;
			assignment = j;
		}
	}
	dist[0] = mindist;
	assert(assignment<nclus);
	return(assignment);
}


double kmeans(double *CX,const double *X,unsigned int *c,unsigned int dim,unsigned int npts,unsigned int nclus,unsigned int maxiter)
{
	double mindist = 0.0;

	/* number of points per cluster */
	unsigned int *CN = (unsigned int *) calloc(nclus, sizeof(unsigned int)); 
	assert(CN);
	
	/* old assignement of points to cluster */
	unsigned int *old_c = (unsigned int *) malloc(npts* sizeof(unsigned int));
	assert(old_c);

	/* assign to value which is out of range */
	for ( unsigned int i=0 ; i<npts ; i++)
		old_c[i] = nclus;

	unsigned int iteration = 0;
	unsigned int nchanged = 1;

	double sse = 0.0;
	const double *px = NULL;
	while ((iteration < maxiter) || (maxiter == 0))
	{
		sse = 0.0;
		/* find nearest cluster center */
		
		px = X;
		for ( unsigned int i=0; i<npts ; i++,px+=dim)
		{
			c[i] = assign_point_to_cluster(px,CX,dim,nclus,&mindist);
			sse += (mindist*mindist);

		}

		/* delete cluster centers */
		for ( unsigned int i=0; i<nclus*dim ; i++)
			CX[i] = 0.0;

		/* count number of points in cluster */
		for ( unsigned int i=0 ; i<nclus ; i++ )
			CN[i] = 0;

		for ( unsigned int i=0 ; i<npts ; i++ )
			CN[c[i]]++;

		/* assign points to empty cluster */
		for ( unsigned int i=0 ; i<nclus ; i++ )
		{
			if (CN[i] > 0) continue;

			/* search for cluster with more than one point */
			unsigned int j = 0;
			while (j<npts && CN[c[j]]<2) j++;
			/* no cluster with more than one member, others will remain emtpy */
			if (j==npts) break;
#ifdef KMEANS_DEBUG
			printf("empty cluster [%d], filling it with point [%d]\n",j,i);
#endif
			/* assign point to the empty cluster */
			CN[c[j]]--;
			c[j] = i; 
			CN[i]++;
		}

		/* add points to cluster centers */
		px = X;
		for ( unsigned int i=0 ; i<npts ; i++,px+=dim )
		{
			double *pcx = CX + c[i]*dim;
			for ( unsigned int k=0 ; k<dim ; k++ )
				pcx[k] += px[k];
		}
		
		/* calculate mean */
		double *pcx = CX;
		for ( unsigned int i=0 ; i<nclus ; i++,pcx+=dim )
		{
			if (CN[i] > 0)
				for ( unsigned int k=0 ; k<dim ; k++ )
					pcx[k]/=CN[i];
		}

		/* count number of changed points */
		nchanged = 0;
		for ( unsigned int i=0 ; i<npts ; i++ ) 
			if (c[i] != old_c[i]) nchanged++;

		/* no points changed: done */
		if (nchanged==0) break;

#ifdef KMEANS_VERBOSE
		printf("iteration %4d, #(changed points): %4d, sse: %4g\n",iteration,nchanged,sse);
#endif

		memcpy(old_c,c,npts*sizeof(unsigned int));
		iteration++;

	}

#ifdef KMEANS_VERBOSE
		printf("iteration %4d, #(changed points): %4d, sse: %4g\n",iteration,nchanged,sse);
#endif
	
	/* find nearest cluster center if maxiter was not reached */
	if (nchanged>0)
	{
		sse = 0.0;
		const double *px = X;
		for (unsigned int i=0; i<npts ; i++,px+=dim)
		{
			c[i] = assign_point_to_cluster(px,CX,dim,nclus,&mindist);
			sse += (mindist*mindist);
		}
	}

	free(CN);
	free(old_c);
		
	return(sse);
}


void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[])
{

	unsigned int	npts, dim, nclus;
	const double	*X; 
	double			*CXp, *psse;
	int				i;
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

	if ((nlhs > 3) || (nlhs < 1)){
		mexPrintf("minimal one, maximal three output arguments expected.");
		return;
	}

	if (nlhs>1) /* sse needs to be calculated */
	{
		plhs[1] = mxCreateScalarDouble(0.0);
		psse = mxGetPr(plhs[1]);
	}


	if (!mxIsDouble(prhs[0]) || mxIsComplex(prhs[0]) ||
		mxGetNumberOfDimensions(prhs[0]) != 2)
	{
		mexPrintf("input 1 (X) must be a real double matrix");
		return;
	}

	dim = mxGetM(prhs[0]);
	npts = mxGetN(prhs[0]);


	if (!mxIsDouble(prhs[1]) || mxIsComplex(prhs[1]) ||
		mxGetNumberOfDimensions(prhs[1]) != 2 ||
		mxGetM(prhs[1]) != dim)
	{
		mexPrintf("input 2 (CX) must be a real double matrix compatible with input 1 (X)");
		return;
	}

	nclus = mxGetN(prhs[1]);

	plhs[0] = mxCreateDoubleMatrix(dim, nclus, mxREAL);
	CXp = mxGetPr(plhs[0]);

	/* input points */
	X = mxGetPr(prhs[0]);

	/* copy initial guess to CXp */
	memcpy(CXp,mxGetPr(prhs[1]),dim*nclus*sizeof(double));

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

	/* start kmeans */
	double sse = kmeans(CXp,X,assignment,dim,npts,nclus,maxiter);

	if (nlhs>1)
		psse[0] = sse;
	
	if (nlhs>2) /* return also the assignment */
	{
		for (unsigned int i=0; i<npts; i++)
			assignment[i]++;
	}
	else
		free(assignment);
}




