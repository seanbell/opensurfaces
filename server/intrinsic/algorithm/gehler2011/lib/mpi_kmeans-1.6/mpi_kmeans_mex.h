#ifndef __MPI_KMEANS_MEX_H__
#define __MPI_KMEANS_MEX_H__

double compute_distance(const double *vec1, const double *vec2, const unsigned int dim);
void compute_cluster_distances(PREC *dist, PREC *s, const double *CX, unsigned int dim,unsigned int nclus, const bool *cluster_changed);
void add_point_to_cluster(double *pcxp, unsigned int *CN, const double *px, const unsigned int dim);
void remove_point_from_cluster(double *pcxp, unsigned int *CN, const double *px, const unsigned int dim);
double compute_sserror(const double *CX, const double *X, const unsigned int *c,unsigned int dim, unsigned int npts);
double init_point_to_cluster(unsigned int *c, PREC2 *mindist, PREC *low_b,const PREC *dist, const double *CX, const double *px, unsigned int dim, unsigned int nclus);
void find_nearest_cluster_center(unsigned int *c, const double *CX, const double *px, const PREC *dist, PREC2 *mindist, PREC *low_b, PREC *s, bool *up_to_date, unsigned int dim, unsigned int nclus);
double kmeans(double *CXp,const double *X,unsigned int *c,unsigned int dim,unsigned int npts,unsigned int nclus,unsigned int maxiter);


#endif


