#!/usr/bin/python
# Cython wrapper for the MPI-Kmeans library by Peter Gehler
# (C) by Thomas Wiecki (wiecki@tuebingen.mpg.de), 2008
# Based on the wrapper code of Christoph Lampert (christoph.lampert@tuebingen.mpg.de).
# GPLv2 or later.

from __future__ import division
import numpy as np
cimport numpy as np

# Define data type
DTYPE = np.double
ctypedef np.double_t DTYPE_t

# Define library call
cdef extern from "mpi_kmeans.h":
    double c_kmeans "kmeans" (double *CX, double *X,unsigned int *assignment,unsigned int dim,unsigned int npts,unsigned int nclus,unsigned int maxiter, unsigned int nr_restarts)

from ctypes import c_uint, c_double

def kmeans(np.ndarray[DTYPE_t, ndim=2] X, unsigned int num_clusters, unsigned int maxiter=0, unsigned int num_runs=1):
    """Cython wrapper for Peter Gehlers accelerated MPI-Kmeans routine.
    centroids, dist, assignments = kmeans(X, num_clusters, maxiter=0, num_runs=1)

    --Input--
    X            : input data (2D numpy array)
    num_clusters : number of centroids to use (k)
    [maxiter]    : how many iterations to run (setting this to 0 will run kmeans until it converges) (default is 0).
    [num_runs}   : how many times to restart the clustering (default is 1).

    --Output--
    centroids    : the cluster centers
    dist         : the sum squared error
    assignments  : the centroids that were assigned to each data point
    
    Example:
    import py_kmeans
    import numpy as np
    X = np.array( np.random.rand(4,3) )
    clusters, dist, labels = py_kmeans.kmeans(X, 2)"""

    # Initializing
    cdef unsigned int num_points = X.shape[0]
    cdef unsigned int dim = X.shape[1]
    cdef double dist
    num_clusters = <unsigned int> min(num_clusters, num_points)

    # Init output array for assignments
    cdef np.ndarray assignments=np.empty( (num_points), dtype=c_uint, order='C')

    # Init output array for cluster centroids
    permutation = np.random.permutation( range(num_points) )
    cdef np.ndarray[DTYPE_t, ndim=2] centroids = np.array(X[permutation[:num_clusters],:], order='C')

    # Call mpi_kmeans routine
    dist = c_kmeans( <double *> centroids.data, <double *> X.data,
		  <unsigned int *> assignments.data, dim, num_points,
		  num_clusters, maxiter, num_runs)

    return centroids, dist, (assignments+1)


def test():
    #np.random.seed(1)
    X = np.array( np.random.rand(4,3) )
    print X
    clst,dist,labels = kmeans(X, 2)
    
    print "cluster centers=\n",clst
    print "dist=",dist
    print "cluster labels",labels
