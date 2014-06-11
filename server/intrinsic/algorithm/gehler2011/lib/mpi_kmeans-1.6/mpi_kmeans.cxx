#include <stdio.h>
#include <stdlib.h>
#include <float.h>
#include <memory.h>
#include <math.h>
#include <assert.h>
#include "mpi_kmeans.h"

#if KMEANS_VERBOSE>1
unsigned int saved_two=0,saved_three_one=0,saved_three_two=0,saved_three_three=0,saved_three_b=0;
#endif


void kmeans_error(char *msg)
{
	printf("%s",msg);
	exit(-1);
}

int comp_randperm (const void * a, const void * b)
{
	return ((int)( *(double*)a - *(double*)b ));
}


void randperm(unsigned int *order, unsigned int npoints)
{
	double *r = (double*)malloc(2*npoints*sizeof(double));
	for (unsigned int i=0; i<2*npoints; i++,i++)
	{
		r[i] = rand();
		r[i+1] = i/2;
	}
	qsort (r, npoints, 2*sizeof(double), comp_randperm);

	for (unsigned int i=1; i<2*npoints; i++,i++)
		order[i/2] = (unsigned int)r[i];

	free(r);
}

PREC compute_distance(const PREC *vec1, const PREC *vec2, const unsigned int dim)
{
	PREC d = 0.0;
	for ( unsigned int k=0 ; k<dim ; k++ )
	{
		PREC df = (vec1[k]-vec2[k]);
		d += df*df;
	}
	if (d<0.0){
		printf("d = %g\n",d);
		for (unsigned int k=0; k<dim ; k++)
			printf("vec1[%d] = %g, vec2[%d] = %g\n",k,vec1[k],k,vec2[k]);
	}
	assert(d>=0.0);
	d = sqrt(d);

	return d;
}

PREC compute_sserror(const PREC *CX, const PREC *X, const unsigned int *c,unsigned int dim, unsigned int npts)
{
	PREC sse = 0.0;
	const PREC *px = X;
	for ( unsigned int i=0 ; i<npts ; i++,px+=dim)
	{
		const PREC *pcx = CX+c[i]*dim;
		PREC d = compute_distance(px,pcx,dim);
		sse += d*d;
	}
	assert(sse>=0.0);
	return(sse);
}

PREC compute_sserror_w(const PREC *CX, const PREC *X, const W_PREC *W, const unsigned int *c,unsigned int dim, unsigned int npts)
{
	PREC sse = 0.0;
	const PREC *px = X;
	for ( unsigned int i=0 ; i<npts ; i++,px+=dim)
	{
		const PREC *pcx = CX+c[i]*dim;
		PREC d = compute_distance(px,pcx,dim);
		sse += (W==NULL)?d*d:(PREC)(W[i])*d*d;
	}
	assert(sse>=0.0);
	return(sse);
}


void remove_point_from_cluster(unsigned int cluster_ind, PREC *CX, const PREC *px, unsigned int *nr_points, unsigned int dim)
{
	PREC *pcx = CX + cluster_ind*dim;

	/* empty cluster after or before removal */
	if (nr_points[cluster_ind]<2)
	{
		for ( unsigned int k=0 ; k<dim ; k++ )
			pcx[k] = 0.0;
		nr_points[cluster_ind]=0;
	}
	else
	{
		/* pgehler: remove PREC here */
		PREC nr_old,nr_new; 
		nr_old = (PREC)nr_points[cluster_ind];
		(nr_points[cluster_ind])--;
		nr_new = (PREC)nr_points[cluster_ind];

		for ( unsigned int k=0 ; k<dim ; k++ )
			pcx[k] = (nr_old*pcx[k] - px[k])/nr_new;
	}
}
void remove_point_from_cluster_w(unsigned int cluster_ind, PREC *CX, const PREC *px, const W_PREC *W, W_PREC *nr_points_weighted, unsigned int point_ind, unsigned int *nr_points, unsigned int dim)
{
	PREC *pcx = CX + cluster_ind*dim;

	/* empty cluster after or before removal */
	if (nr_points[cluster_ind]<2)
	{
		for ( unsigned int k=0 ; k<dim ; k++ )
			pcx[k] = 0.0;
		nr_points[cluster_ind]=0;
		if (nr_points_weighted != NULL)
			nr_points_weighted[cluster_ind] = 0;
	}
	else
	{
	    (nr_points[cluster_ind])--;

		PREC nr_old = (PREC)(nr_points_weighted[cluster_ind]);
        (nr_points_weighted[cluster_ind])-= W[point_ind];
		PREC nr_new = (PREC)(nr_points_weighted[cluster_ind]);

		for ( unsigned int k=0 ; k<dim ; k++ )
			pcx[k] = (nr_old*pcx[k] - ((PREC)(W[point_ind]))*px[k])/nr_new;
	}
}


void add_point_to_cluster(unsigned int cluster_ind, PREC *CX, const PREC *px, unsigned int *nr_points, unsigned int dim)
{

	PREC *pcx = CX + cluster_ind*dim;

	/* first point in cluster */
	if (nr_points[cluster_ind]==0)
	{		
		(nr_points[cluster_ind])++;
		for ( unsigned int k=0 ; k<dim ; k++ )
			pcx[k] = px[k];
	}
	else
	{
/* remove PREC here */
		PREC nr_old = (PREC)(nr_points[cluster_ind]);
		(nr_points[cluster_ind])++;
		PREC nr_new = (PREC)(nr_points[cluster_ind]);
		for ( unsigned int k=0 ; k<dim ; k++ )
			pcx[k] = (nr_old*pcx[k]+px[k])/nr_new;
	}
}

void add_point_to_cluster_w(unsigned int cluster_ind, PREC *CX, const PREC *px, const W_PREC *W, W_PREC *nr_points_weighted, unsigned int point_ind, unsigned int *nr_points, unsigned int dim)
{

	PREC *pcx = CX + cluster_ind*dim;

	/* first point in cluster */
	if (nr_points[cluster_ind]==0)
	{
		(nr_points[cluster_ind])++;
		(nr_points_weighted[cluster_ind]) = W[point_ind];
		for ( unsigned int k=0 ; k<dim ; k++ )
			pcx[k] = (PREC)(px[k]);

	}
	else
	{
	    (nr_points[cluster_ind])++;

		PREC nr_old = (PREC)(nr_points_weighted[cluster_ind]);
        (nr_points_weighted[cluster_ind])+= W[point_ind];
		PREC nr_new = (PREC)(nr_points_weighted[cluster_ind]);

		for ( unsigned int k=0 ; k<dim ; k++ )
			pcx[k] = (nr_old*pcx[k] + ((PREC)(W[point_ind]))*((PREC)(px[k])))/nr_new;
	}
}



bool remove_identical_clusters(PREC *CX, BOUND_PREC *cluster_distance, const PREC *X, unsigned int *cluster_count, unsigned int *c, unsigned int dim, unsigned int nclus, unsigned int npts)
{
	bool stat = false;
	for ( unsigned int i=0 ; i<(nclus-1) ; i++ )
	{
		for ( unsigned int j=i+1 ; j<nclus ; j++ )
		{
			if (cluster_distance[i*nclus+j] <= BOUND_EPS)
			{
#if KMEANS_VERBOSE>1
				printf("found identical cluster : %d\n",j);
#endif
				stat = true;
				/* assign the points from j to i */
				const PREC *px = X;
				for ( unsigned int n=0 ; n<npts ; n++,px+=dim )
				{
					if (c[n] != j) continue;
					remove_point_from_cluster(c[n],CX,px,cluster_count,dim);
					c[n] = i;
					add_point_to_cluster(c[n],CX,px,cluster_count,dim);
				}
			}
		}
	}
	return(stat);
}

bool remove_identical_clusters_w(PREC *CX, BOUND_PREC *cluster_distance, const PREC *X, const W_PREC *W, W_PREC *nr_points_weighted, unsigned int *cluster_count, unsigned int *c, unsigned int dim, unsigned int nclus, unsigned int npts)
{
	bool stat = false;
	for ( unsigned int i=0 ; i<(nclus-1) ; i++ )
	{
		for ( unsigned int j=i+1 ; j<nclus ; j++ )
		{
			if (cluster_distance[i*nclus+j] <= BOUND_EPS)
			{
#if KMEANS_VERBOSE>0
				printf("found identical cluster : %d\n",j);
#endif
				stat = true;
				/* assign the points from j to i */
				const PREC *px = X;
				for ( unsigned int n=0 ; n<npts ; n++,px+=dim )
				{
					if (c[n] != j) continue;
					remove_point_from_cluster_w(c[n],CX,px,W,nr_points_weighted,n,cluster_count,dim);
					c[n] = i;
					add_point_to_cluster_w(c[n],CX,px,W,nr_points_weighted,n,cluster_count,dim);
				}
			}
		}
	}
	return(stat);
}



void compute_cluster_distances(BOUND_PREC *dist, BOUND_PREC *s, const PREC *CX, unsigned int dim,unsigned int nclus, const bool *cluster_changed)
{
	for ( unsigned int j=0 ; j<nclus ; j++ )
		s[j] = BOUND_PREC_MAX;

	const PREC *pcx = CX;
	for ( unsigned int i=0 ; i<nclus-1 ; i++,pcx+=dim)
	{
		const PREC *pcxp = CX + (i+1)*dim;
		unsigned int cnt=i*nclus+i+1;
		for ( unsigned int j=i+1 ; j<nclus; j++,cnt++,pcxp+=dim )
		{
			if (cluster_changed[i] || cluster_changed[j])
			{
				dist[cnt] = (BOUND_PREC)(0.5 * compute_distance(pcx,pcxp,dim));
				dist[j*nclus+i] = dist[cnt];

				if (dist[cnt] < s[i])
					s[i] = dist[cnt];

				if (dist[cnt] < s[j])
					s[j] = dist[cnt];
			}
		}
	}

}

unsigned int init_point_to_cluster_w(unsigned int point_ind, const PREC *px, const PREC *CX, unsigned int dim,unsigned int nclus, PREC *mindist, BOUND_PREC *low_b, unsigned int n_low_b, const BOUND_PREC *cl_dist)
{
	unsigned int bias = point_ind*n_low_b;

	const PREC *pcx = CX;
	PREC mind = compute_distance(px,pcx,dim);
	if (n_low_b>0) low_b[bias] = (BOUND_PREC)mind;
	unsigned int assignment = 0;
	pcx+=dim;
	for ( unsigned int j=1 ; j<nclus ; j++,pcx+=dim )
	{
		if (mind + BOUND_EPS <= cl_dist[assignment*nclus+j])
			continue;

		PREC d = compute_distance(px,pcx,dim);
		if (n_low_b>0) low_b[j+bias] = (BOUND_PREC)d;

		if (d<mind)
		{
			mind = d;
			assignment = j;
		}
	}
	mindist[point_ind] = mind;
	return(assignment);
}

unsigned int init_point_to_cluster(unsigned int point_ind, const PREC *px, const PREC *CX, unsigned int dim,unsigned int nclus, PREC *mindist, BOUND_PREC *low_b, const BOUND_PREC *cl_dist)
{
	bool use_low_b = true;

	if (low_b==NULL) use_low_b = false;
	unsigned int bias = point_ind*nclus;
	
	const PREC *pcx = CX;
	PREC mind = compute_distance(px,pcx,dim);
	if (use_low_b) low_b[bias] = (BOUND_PREC)mind;
	unsigned int assignment = 0;
	pcx+=dim;
	for ( unsigned int j=1 ; j<nclus ; j++,pcx+=dim )
	{
		if (mind + BOUND_EPS <= cl_dist[assignment*nclus+j])
			continue;

		PREC d = compute_distance(px,pcx,dim);
		if(use_low_b) low_b[j+bias] = (BOUND_PREC)d;

		if (d<mind)
		{
			mind = d;
			assignment = j;
		}
	}
	mindist[point_ind] = mind;
	return(assignment);
}

unsigned int assign_point_to_cluster_ordinary(const PREC *px, const PREC *CX, unsigned int dim,unsigned int nclus)
{
	unsigned int assignment = nclus;
	PREC mind = PREC_MAX;
	const PREC *pcx = CX;
	for ( unsigned int j=0 ; j<nclus ; j++,pcx+=dim )
	{
		PREC d = compute_distance(px,pcx,dim);
		if (d<mind)
		{
			mind = d;
			assignment = j;
		}
	}
	assert(assignment < nclus);
	return(assignment);
}

unsigned int assign_point_to_cluster_w(unsigned int point_ind, const PREC *px, const PREC *CX, unsigned int dim,unsigned int nclus, unsigned int old_assignment, PREC *mindist, BOUND_PREC *s, BOUND_PREC *cl_dist, BOUND_PREC *low_b, unsigned int n_low_b)
{
	bool up_to_date = false;

	unsigned int bias = point_ind*n_low_b;

	PREC mind = mindist[point_ind];

	if (mind+BOUND_EPS <= s[old_assignment])
	{
#ifdef KMEANS_DEBUG
		saved_two++;
#endif
		return(old_assignment);
	}

	unsigned int assignment = old_assignment;
	unsigned int counter = assignment*nclus;
	const PREC *pcx = CX;
	for ( unsigned int j=0 ; j<nclus ; j++,pcx+=dim )
	{
		if (j==old_assignment)
		{
#ifdef KMEANS_DEBUG
			saved_three_one++;
#endif
			continue;
		}

		if ((n_low_b>0) &&(j<n_low_b)&& (mind+BOUND_EPS <= low_b[j+bias]))
		{
#ifdef KMEANS_DEBUG
			saved_three_two++;
#endif
			continue;
		}

		if (mind+BOUND_EPS <= cl_dist[counter+j])
		{
#ifdef KMEANS_DEBUG
			saved_three_three++;
#endif
			continue;
		}

		PREC d = 0.0;
		if (!up_to_date)
		{
			d = compute_distance(px,CX+assignment*dim,dim);
			mind = d;
			if ((n_low_b>0)&&(assignment<n_low_b)) low_b[assignment+bias] = (BOUND_PREC)d;
			up_to_date = true;
		}

		if ((n_low_b==0)||(j>=n_low_b))
			d = compute_distance(px,pcx,dim);
		else if ((mind > BOUND_EPS+low_b[j+bias]) || (mind > BOUND_EPS+cl_dist[counter+j]))
		{
			d =compute_distance(px,pcx,dim);
			low_b[j+bias] = (BOUND_PREC)d;
		}
		else
		{
#ifdef KMEANS_DEBUG
			saved_three_b++;
#endif
			continue;
		}

		if (d<mind)
		{
			mind = d;
			assignment = j;
			counter = assignment*nclus;
			up_to_date = true;
		}
	}
	mindist[point_ind] = mind;

	return(assignment);
}


unsigned int assign_point_to_cluster(unsigned int point_ind, const PREC *px, const PREC *CX, unsigned int dim,unsigned int nclus, unsigned int old_assignment, PREC *mindist, BOUND_PREC *s, BOUND_PREC *cl_dist, BOUND_PREC *low_b)
{
	bool up_to_date = false,use_low_b=true;;

	unsigned int bias = point_ind*nclus;
	if (low_b==NULL)use_low_b=false;

	PREC mind = mindist[point_ind];

	if (mind+BOUND_EPS <= s[old_assignment])
	{
#ifdef KMEANS_VEBOSE
		saved_two++;
#endif
		return(old_assignment);
	}

	unsigned int assignment = old_assignment;
	unsigned int counter = assignment*nclus;
	const PREC *pcx = CX;
	for ( unsigned int j=0 ; j<nclus ; j++,pcx+=dim )
	{
		if (j==old_assignment)
		{
#if KMEANS_VERBOSE>1
			saved_three_one++;
#endif
			continue;
		}
		
		if (use_low_b && (mind+BOUND_EPS <= low_b[j+bias]))
		{
#if KMEANS_VERBOSE>1
			saved_three_two++;
#endif
			continue;
		}

		if (mind+BOUND_EPS <= cl_dist[counter+j])
		{
#if KMEANS_VERBOSE>1
			saved_three_three++;
#endif
			continue;
		}

		PREC d = 0.0;
		if (!up_to_date)
		{
			d = compute_distance(px,CX+assignment*dim,dim);
			mind = d;
			if(use_low_b) low_b[assignment+bias] = (BOUND_PREC)d;
			up_to_date = true;
		}
		
		if (!use_low_b)
			d = compute_distance(px,pcx,dim);
		else if ((mind > BOUND_EPS+low_b[j+bias]) || (mind > BOUND_EPS+cl_dist[counter+j]))
		{
			d =compute_distance(px,pcx,dim);
			low_b[j+bias] = (BOUND_PREC)d;
		}
		else
		{
#if KMEANS_VERBOSE>1
			saved_three_b++;
#endif
			continue;
		}

		if (d<mind)
		{
			mind = d;
			assignment = j;
			counter = assignment*nclus;
			up_to_date = true;
		}
	}
	mindist[point_ind] = mind;

	return(assignment);
}


PREC kmeans_run_w(PREC *CX,const PREC *X, const W_PREC *W, unsigned int *c,unsigned int dim,unsigned int npts,unsigned int nclus,unsigned int maxiter)
{

	PREC *tCX = (PREC *)calloc(nclus * dim, sizeof(PREC));
	assert(tCX);

	/* number of points per cluster */
	unsigned int *CN = (unsigned int *) calloc(nclus, sizeof(unsigned int));
	assert(CN);

    /*the sum of the weights of the points per cluster */
    W_PREC *CN_weighted = (W_PREC *) calloc(nclus, sizeof(W_PREC));
    assert(CN_weighted);

	/* old assignement of points to cluster */
	unsigned int *old_c = (unsigned int *) malloc(npts* sizeof(unsigned int));
	assert(old_c);

	/* assign to value which is out of range */
	for ( unsigned int i=0 ; i<npts ; i++)
		old_c[i] = nclus;

#if KMEANS_VERBOSE>0
	printf("compile without setting the KMEANS_VERBOSE flag for no output\n");
#endif

    bool use_low_b = false;
    unsigned int nr_low_b = nclus;
    BOUND_PREC *low_b;

    while ((!use_low_b)&&(nr_low_b>0))
    {
        low_b = (BOUND_PREC *) calloc(npts*nr_low_b,sizeof(BOUND_PREC));

        if (low_b == NULL)
        {
#if KMEANS_VERBOSE>0
            printf("Not enough memory for [%d] lower bounds, will compute with less\n",nr_low_b);
#endif
            use_low_b = false;
            nr_low_b--;
        }
        else
        {
            use_low_b = true;
            assert(low_b);
        }
    }

#if KMEANS_VERBOSE>0
    if (nr_low_b == 0)
        printf("Not enough memory for lower bounds, will compute without\n",nr_low_b);
#endif

	BOUND_PREC *cl_dist = (BOUND_PREC *)calloc(nclus*nclus, sizeof(BOUND_PREC));
	assert(cl_dist);

	BOUND_PREC *s = (BOUND_PREC *) malloc(nclus*sizeof(BOUND_PREC));
	assert(s);

	BOUND_PREC *offset = (BOUND_PREC *) malloc(nclus * sizeof(BOUND_PREC)); /* change in distance of a cluster mean after a iteration */
	assert(offset);

	PREC *mindist = (PREC *)malloc(npts * sizeof(PREC));
	assert(mindist);
	for ( unsigned int i=0;i<npts;i++)
		mindist[i] = PREC_MAX;

	bool *cluster_changed = (bool *) malloc(nclus * sizeof(bool)); /* did the cluster change? */
	assert(cluster_changed);
	for ( unsigned int j=0 ; j<nclus ; j++ )
		cluster_changed[j] = true;

	termination_reason term_reason = NO_TERMINATION;

	unsigned int iteration = 0;
	unsigned int nchanged = 1;
	while (iteration < maxiter || maxiter == 0)
	{

		/* compute cluster-cluster distances */
		compute_cluster_distances(cl_dist, s, CX, dim,nclus, cluster_changed);

		/* assign all points from identical clusters to the first occurence of that cluster */
		remove_identical_clusters_w(CX, cl_dist, X, W, CN_weighted, CN, old_c, dim, nclus, npts);

		/* find nearest cluster center */
		if (iteration == 0)
		{

		  const PREC *px = X;
		  for ( unsigned int i=0 ; i<npts ; i++,px+=dim)
			{
				c[i] = init_point_to_cluster_w(i,px,CX,dim,nclus,mindist,low_b,nr_low_b,cl_dist);
				add_point_to_cluster_w(c[i],tCX,px,W,CN_weighted,i,CN,dim);
			}
			nchanged = npts;
		}
		else
		{
			for ( unsigned int j=0 ; j<nclus ; j++)
				cluster_changed[j] = false;

			nchanged = 0;
			const PREC *px = X;
			for ( unsigned int i=0 ; i<npts ; i++,px+=dim)
			{
				c[i] = assign_point_to_cluster_w(i,px,CX,dim,nclus,old_c[i],mindist,s,cl_dist,low_b,nr_low_b);

				if (old_c[i] == c[i]) continue;

				nchanged++;

				cluster_changed[c[i]] = true;
				cluster_changed[old_c[i]] = true;

				remove_point_from_cluster_w(old_c[i],tCX,px,W,CN_weighted,i,CN,dim);
				add_point_to_cluster_w(c[i],tCX,px,W,CN_weighted,i,CN,dim);
			}

		}


		/* fill up all empty clusters */
		unsigned int nof_empty = 0; /* count number of empty clusters */
		unsigned int nof_filled = 0; /* count number of filled clusters */
		for ( unsigned int j=0 ; j<nclus ; j++)
		{
			if (CN[j]>0) continue;
			++nof_empty;

			unsigned int  *rperm = (unsigned int*)malloc(npts*sizeof(unsigned int));
			assert(rperm);
			randperm(rperm,npts);

			/* search first point that is 
			   - in a cluster with more than two points
			   - not identical to a cluster center
			   and assign it as a new cluster center
			   
			   better would be to split the cluster with highest sse
			*/
			unsigned int i=0;
			unsigned int indx = rperm[0];
			for (i=0; i<npts; ++i)
			{
				/* more than two points ? */
				if (CN[c[rperm[i]]]<2)
					continue;
				/* identical to cluster center ? */
				bool same = false;
				PREC *pcx = CX;
				indx = rperm[i]; 
				const PREC *px = X + indx*dim;
				for (unsigned int k=0; k<nclus; ++k)
					same = same || (compute_distance(pcx+k*dim,px,dim) < BOUND_EPS);
				if (same) continue;

				/* we found a point */
				break;
			}
			free(rperm);

			/* there is no such point. Probably there are less 
			   distinct points than cluster centers to be assigned. 
			   We may still be able to correct another empty cluster 
			   but will terminate after this iteration. (because nof_empty!=nof_filled) . */
			if (i==npts)
				continue;

#ifdef KMEANS_DEBUG
			printf("empty cluster [%d], filling it with point [%d]\n",j,i);
#endif

			const PREC *px = X + indx*dim;
			cluster_changed[c[indx]] = true;
			cluster_changed[j] = true;
			remove_point_from_cluster(c[indx],tCX,px,CN,dim);
			c[indx] = j;
			add_point_to_cluster_w(j,tCX,px,W,CN_weighted,indx,CN,dim);
			/* void the bounds */
			s[j] = (BOUND_PREC)0.0;
			mindist[indx] = 0.0;
			if (use_low_b)
				for ( unsigned int k=0 ; k<npts ; k++ )
					low_b[k*nclus+j] = (BOUND_PREC)0.0;

			nchanged++;
			++nof_filled;
		}

		/* could we fill all empty clusters? If not we have fewer different points than clusters requested */
		if (nof_empty!=nof_filled)
		{
			term_reason = EMPTY_CLUSTERS;
			break;
		}

		/* no assignment changed: done */
		if (nchanged==0)
		{
			term_reason = CONVERGED;
			break;
		}

		/* compute the offset */

		PREC *pcx = CX;
		PREC *tpcx = tCX;
		for ( unsigned int j=0 ; j<nclus ; j++,pcx+=dim,tpcx+=dim )
		{
			offset[j] = (BOUND_PREC)0.0;
			if (cluster_changed[j])
			{
				offset[j] = (BOUND_PREC)compute_distance(pcx,tpcx,dim);
				memcpy(pcx,tpcx,dim*sizeof(PREC));
			}
		}

		/* update the lower bound */
		if (use_low_b)
		{
			for ( unsigned int i=0,cnt=0 ; i<npts ; i++ )
				for ( unsigned int j=0 ; j<nclus ; j++,cnt++ )
				{
					low_b[cnt] -= offset[j];
					if (low_b[cnt]<(BOUND_PREC)0.0) low_b[cnt] = (BOUND_PREC)0.0;
				}
		}

		for ( unsigned int i=0; i<npts; i++)
			mindist[i] += (PREC)offset[c[i]];

		memcpy(old_c,c,npts*sizeof(unsigned int));

#if KMEANS_VERBOSE>0
		PREC sse = compute_sserror(CX,X,c,dim,npts);
		printf("iteration %4d, #(changed points): %4d, sse: %4.2f\n",(int)iteration,(int)nchanged,sse);
#endif

#ifdef KMEANS_DEBUG
		printf("saved at 2) %d\n",saved_two);
		printf("saved at 3i) %d\n",saved_three_one);
		printf("saved at 3ii) %d\n",saved_three_two);
		printf("saved at 3iii) %d\n",saved_three_three);
		printf("saved at 3b) %d\n",saved_three_b);
		saved_two=0;
		saved_three_one=0;
		saved_three_two=0;
		saved_three_three=0;
		saved_three_b=0;
#endif

		iteration++;
		if (iteration == maxiter)
			term_reason = MAX_ITER;

	}
	assert(term_reason != NO_TERMINATION);
	if (term_reason != EMPTY_CLUSTERS)
		for ( unsigned int j=0;j<nclus;j++)
			assert(CN[j]>0);


	/* find nearest cluster center if iteration reached maxiter */
	if (term_reason == MAX_ITER)
	{
		assert(nchanged > 0);
	    const PREC *px = X;
		for ( unsigned int i=0 ; i<npts ; i++,px+=dim)
			c[i] = assign_point_to_cluster_ordinary(px,CX,dim,nclus);
	  }
	PREC sse = compute_sserror_w(CX,X,W,c,dim,npts);

#if KMEANS_VERBOSE>0
	printf("iteration %4d, #(changed points): %4d, sse: %4.2f\n",(int)iteration,(int)nchanged,sse);
#endif

	if(low_b) free(low_b);
	free(cluster_changed);
	free(mindist);
	free(s);
	free(offset);
	free(cl_dist);
	free(tCX);
	free(CN);
	free(CN_weighted);
	free(old_c);

	return(sse);
}


PREC kmeans_run(PREC *CX,const PREC *X,unsigned int *c,unsigned int dim,unsigned int npts,unsigned int nclus,unsigned int maxiter)
{
	PREC *tCX = (PREC *)calloc(nclus * dim, sizeof(PREC));
	if (tCX==NULL)	kmeans_error((char*)"Failed to allocate mem for Cluster points");

	/* number of points per cluster */
	unsigned int *CN = (unsigned int *) calloc(nclus, sizeof(unsigned int)); 
	if (CN==NULL)	kmeans_error((char*)"Failed to allocate mem for assignment");
	
	/* old assignement of points to cluster */
	unsigned int *old_c = (unsigned int *) malloc(npts* sizeof(unsigned int));
	if (old_c==NULL)	kmeans_error((char*)"Failed to allocate mem for temp assignment");

	/* assign to value which is out of range */
	for ( unsigned int i=0 ; i<npts ; i++)
		old_c[i] = nclus;

#if KMEANS_VERBOSE>0
	printf("compile without setting the KMEANS_VERBOSE flag for no output\n");
#endif

	BOUND_PREC *low_b = (BOUND_PREC *) calloc(npts*nclus,sizeof(BOUND_PREC));
	bool use_low_b = false;
	if (low_b == NULL)
	{
#if KMEANS_VERBOSE>0
		printf("not enough memory for lower bound, will compute without\n");
#endif
		use_low_b = false;
	}
	else
	  {
	    use_low_b = true;
	    assert(low_b);
	  }


	BOUND_PREC *cl_dist = (BOUND_PREC *)calloc(nclus*nclus, sizeof(BOUND_PREC));
	if (cl_dist==NULL)	kmeans_error((char*)"Failed to allocate mem for cluster-cluster distance");

	BOUND_PREC *s = (BOUND_PREC *) malloc(nclus*sizeof(BOUND_PREC));
	if (s==NULL)	kmeans_error((char*)"Failed to allocate mem for assignment");

	BOUND_PREC *offset = (BOUND_PREC *) malloc(nclus * sizeof(BOUND_PREC)); /* change in distance of a cluster mean after a iteration */
	if (offset==NULL)	kmeans_error((char*)"Failed to allocate mem for bound points-nearest cluster");

	PREC *mindist = (PREC *)malloc(npts * sizeof(PREC));
	if (mindist==NULL)	kmeans_error((char*)"Failed to allocate mem for bound points-clusters");

	for ( unsigned int i=0;i<npts;i++)
		mindist[i] = PREC_MAX;

	bool *cluster_changed = (bool *) malloc(nclus * sizeof(bool)); /* did the cluster changed? */
	if (cluster_changed==NULL)	kmeans_error((char*)"Failed to allocate mem for variable cluster_changed");
	for ( unsigned int j=0 ; j<nclus ; j++ )
		cluster_changed[j] = true;

	

	unsigned int iteration = 0;
	unsigned int nchanged = 1;
	while (iteration < maxiter || maxiter == 0)
	{
		
		/* compute cluster-cluster distances */
		compute_cluster_distances(cl_dist, s, CX, dim,nclus, cluster_changed);
		
		/* assign all points from identical clusters to the first occurence of that cluster */
		remove_identical_clusters(CX, cl_dist, X, CN, c, dim, nclus, npts);
			
		/* find nearest cluster center */
		if (iteration == 0)
		{
		  
		  const PREC *px = X;
		  for ( unsigned int i=0 ; i<npts ; i++,px+=dim)
			{
				c[i] = init_point_to_cluster(i,px,CX,dim,nclus,mindist,low_b,cl_dist);
				add_point_to_cluster(c[i],tCX,px,CN,dim);
			}
			nchanged = npts;
		}
		else
		{
			for ( unsigned int j=0 ; j<nclus ; j++)
				cluster_changed[j] = false;

			nchanged = 0;
			const PREC *px = X;
			for ( unsigned int i=0 ; i<npts ; i++,px+=dim)
			{
				c[i] = assign_point_to_cluster(i,px,CX,dim,nclus,old_c[i],mindist,s,cl_dist,low_b);

#ifdef KMEANS_DEBUG
				{
					/* If the assignments are not the same, there is still the BOUND_EPS difference 
					   which can be the reason of this*/
					unsigned int tmp = assign_point_to_cluster_ordinary(px,CX,dim,nclus);
					if (tmp != c[i])
					{
						double d1 = compute_distance(px,CX+(tmp*dim),dim);
						double d2 = compute_distance(px,CX+(c[i]*dim),dim);
						assert( (d1>d2)?((d1-d2)<BOUND_EPS):((d2-d1)<BOUND_EPS) );
					}
				}
#endif

				if (old_c[i] == c[i]) continue;
				
				nchanged++;

				cluster_changed[c[i]] = true;
				cluster_changed[old_c[i]] = true;

				remove_point_from_cluster(old_c[i],tCX,px,CN,dim);
				add_point_to_cluster(c[i],tCX,px,CN,dim);
			}

		}


		/* fill up empty clusters */
		for ( unsigned int j=0 ; j<nclus ; j++)
		{
			if (CN[j]>0) continue;
			unsigned int *rperm = (unsigned int*)malloc(npts*sizeof(unsigned int));
			if (cluster_changed==NULL)	kmeans_error((char*)"Failed to allocate mem for permutation");

			randperm(rperm,npts);
			unsigned int i = 0; 
			while (rperm[i]<npts && CN[c[rperm[i]]]<2) i++;
			if (i==npts)continue;
			i = rperm[i];
#if KMEANS_VERBOSE>0
			printf("empty cluster [%d], filling it with point [%d]\n",j,i);
#endif
			cluster_changed[c[rperm[i]]] = true;
			cluster_changed[j] = true;
			const PREC *px = X + i*dim;
			remove_point_from_cluster(c[i],tCX,px,CN,dim);
			c[i] = j;
			add_point_to_cluster(j,tCX,px,CN,dim);
			/* void the bounds */
			s[j] = (BOUND_PREC)0.0;
			mindist[i] = 0.0;
			if (use_low_b)
				for ( unsigned int k=0 ; k<npts ; k++ )
					low_b[k*nclus+j] = (BOUND_PREC)0.0;
			
			nchanged++;
			free(rperm);
		}

		/* no assignment changed: done */
		if (nchanged==0) break; 

		/* compute the offset */

		PREC *pcx = CX;
		PREC *tpcx = tCX;
		for ( unsigned int j=0 ; j<nclus ; j++,pcx+=dim,tpcx+=dim )
		{
			offset[j] = (BOUND_PREC)0.0;
			if (cluster_changed[j])
			{
				offset[j] = (BOUND_PREC)compute_distance(pcx,tpcx,dim);
				memcpy(pcx,tpcx,dim*sizeof(PREC));
			}
		}
		
		/* update the lower bound */
		if (use_low_b)
		{
			for ( unsigned int i=0,cnt=0 ; i<npts ; i++ )
				for ( unsigned int j=0 ; j<nclus ; j++,cnt++ )
				{
					low_b[cnt] -= offset[j];
					if (low_b[cnt]<(BOUND_PREC)0.0) low_b[cnt] = (BOUND_PREC)0.0;
				}
		}

		for ( unsigned int i=0; i<npts; i++)
			mindist[i] += (PREC)offset[c[i]];

		memcpy(old_c,c,npts*sizeof(unsigned int));

#if KMEANS_VERBOSE>0
		PREC sse = compute_sserror(CX,X,c,dim,npts);
		printf("iteration %4d, #(changed points): %4d, sse: %4.2f\n",(int)iteration,(int)nchanged,sse);
#endif

#if KMEANS_VERBOSE>1
		printf("saved at 2) %d\n",saved_two);
		printf("saved at 3i) %d\n",saved_three_one);
		printf("saved at 3ii) %d\n",saved_three_two);
		printf("saved at 3iii) %d\n",saved_three_three);
		printf("saved at 3b) %d\n",saved_three_b);
		saved_two=0;
		saved_three_one=0;
		saved_three_two=0;
		saved_three_three=0;
		saved_three_b=0;
#endif

		iteration++;

	}


#ifdef KMEANS_DEBUG
	for ( unsigned int j=0;j<nclus;j++)
		assert(CN[j]!=0); /* Empty cluster after all */
#endif


	/* find nearest cluster center if iteration reached maxiter */
	if (nchanged>0)
	{
	    const PREC *px = X;
		for ( unsigned int i=0 ; i<npts ; i++,px+=dim)
			c[i] = assign_point_to_cluster_ordinary(px,CX,dim,nclus);
	}
	PREC sse = compute_sserror(CX,X,c,dim,npts);

#if KMEANS_VERBOSE>0
	printf("iteration %4d, #(changed points): %4d, sse: %4.2f\n",(int)iteration,(int)nchanged,sse);
#endif

	if(low_b) free(low_b);
	free(cluster_changed);
	free(mindist);
	free(s);
	free(offset);
	free(cl_dist);
	free(tCX);
	free(CN);
	free(old_c);

	return(sse);
}



PREC kmeans_run_master(PREC *CX,const PREC *X,const W_PREC *W, unsigned int *c,unsigned int dim,unsigned int npts,unsigned int nclus,unsigned int maxiter)
{
	if (W==NULL)
		return (kmeans_run(CX,X,c,dim,npts,nclus,maxiter));
	else
		return (kmeans_run_w(CX,X,W,c,dim,npts,nclus,maxiter));
}


PREC kmeans(PREC *CX,const PREC *X,const W_PREC *W, unsigned int *assignment,unsigned int dim,unsigned int npts,unsigned int nclus,unsigned int maxiter, unsigned int restarts)
{

  if (npts < nclus)
    {
      CX = (PREC*)calloc(nclus*dim,sizeof(PREC));
      memcpy(CX,X,dim*nclus*sizeof(PREC));
      PREC sse = 0.0;
      return(sse);
    }
  else if (npts == nclus)
    {
      memcpy(CX,X,dim*nclus*sizeof(PREC));
      PREC sse = 0.0;
      return(sse);
    }
  else if (nclus == 0)
  {
	  printf("Error: Number of clusters is 0\n");
	  exit(-1);
  }

  /*
   * No starting point is given, generate a new one
   */
  if (CX==NULL)
  {
      unsigned int *order = (unsigned int*)malloc(npts*sizeof(unsigned int));

      CX = (PREC*)calloc(nclus*dim,sizeof(PREC));
      /* generate new starting point */
      randperm(order,npts);
      for (unsigned int i=0; i<nclus; i++)
		  for ( unsigned int k=0; k<dim; k++ )
			  CX[(i*dim)+k] = X[order[i]*dim+k];
      free(order);
		
  }
  assert(CX != NULL);
  
  PREC sse = kmeans_run_master(CX,X,W,assignment,dim,npts,nclus,maxiter);

  unsigned int res = restarts;
  if (res>0)
  {
      PREC minsse = sse;
      unsigned int *order = (unsigned int*)malloc(npts*sizeof(unsigned int));
      PREC *bestCX = (PREC*) malloc(dim*nclus*sizeof(PREC));
      unsigned int *bestassignment = (unsigned int*)malloc(npts*sizeof(unsigned int));

      memcpy(bestCX,CX,dim*nclus*sizeof(PREC));
      memcpy(bestassignment,assignment,npts*sizeof(unsigned int));

      while (res>0)
	  {

		  /* generate new starting point */
		  randperm(order,npts);
		  for (unsigned int i=0; i<nclus; i++)
			  for (unsigned int k=0; k<dim; k++ )
				  CX[(i*dim)+k] = X[order[i]*dim+k];
		
		  sse = kmeans_run_master(CX,X,W,assignment,dim,npts,nclus,maxiter);
		  if (sse<minsse)
		  {
#if KMEANS_VERBOSE>1
			  printf("found a better clustering with sse = %g\n",sse);
#endif
			  minsse = sse;
			  memcpy(bestCX,CX,dim*nclus*sizeof(PREC));
			  memcpy(bestassignment,assignment,npts*sizeof(unsigned int));
		  }
		  res--;

	  }
      memcpy(CX,bestCX,dim*nclus*sizeof(PREC));
      memcpy(assignment,bestassignment,npts*sizeof(unsigned int));
      sse = minsse;
      free(bestassignment);
      free(bestCX);
      free(order);
  }
  assert(CX != NULL);

  return(sse);

}
