#!/usr/bin/python
# Wrapper for the MPI-Kmeans library by Peter Gehler 

from ctypes import c_int, c_double, c_uint
from numpy.ctypeslib import ndpointer
import numpy as N
from numpy import empty,array,reshape,arange

def kmeans(X, nclst, maxiter=0, numruns=1):
    """Wrapper for Peter Gehlers accelerated MPI-Kmeans routine."""
    
    mpikmeanslib = N.ctypeslib.load_library("libmpikmeans.so", ".")
    mpikmeanslib.kmeans.restype = c_double
    mpikmeanslib.kmeans.argtypes = [ndpointer(dtype=c_double, ndim=1, flags='C_CONTIGUOUS'), \
                                    ndpointer(dtype=c_double, ndim=1, flags='C_CONTIGUOUS'), \
                                    ndpointer(dtype=c_uint, ndim=1, flags='C_CONTIGUOUS'), \
                                    c_uint, c_uint, c_uint, c_uint, c_uint ]
    
    npts,dim = X.shape
    assignments=empty( (npts), c_uint )
    
    bestSSE=N.Inf
    bestassignments=empty( (npts), c_uint)
    Xvec = array( reshape( X, (-1,) ), c_double )
    permutation = N.random.permutation( range(npts) ) # randomize order of points
    CX = array(X[permutation[:nclst],:], c_double).flatten()
    SSE = mpikmeanslib.kmeans( CX, Xvec, assignments, dim, npts, min(nclst, npts), maxiter, numruns)
    return reshape(CX, (nclst,dim)), SSE, (assignments+1)


if __name__ == "__main__":
    from numpy import array
    from numpy.random import rand
    
    X = array( rand(12), c_double )
    X.shape = (4,3)
    clst,dist,labels = kmeans(X, 2)
    print "cluster centers=\n",clst
    print "dist=",dist
    print "cluster labels",labels
