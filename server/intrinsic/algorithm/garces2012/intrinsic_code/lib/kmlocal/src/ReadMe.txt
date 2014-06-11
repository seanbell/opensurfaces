See the file ReadMe.txt in the root directory for further information.

Files
-----
KCtree.cpp KCtree.h     For the kc tree
KCutil.cpp KCutil.h     Utilities used in kc-tree construction
KM_ANN.cpp KM_ANN.h     General definitions from ANN
KMcenters.cpp           Center point set
KMcenters.h
KMdata.cpp KMdata.h     Data point set
KMeans.cpp KMeans.h     General definitions for k-means
KMfilterCenters.cpp     Enhanced center set for filtering algorithm
KMfilterCenters.h
KMlocal.cpp KMlocal.h   Algorithms for k-means by local search
KMrand.cpp KMrand.h     Random number generation
KMterm.cpp KMterm.h     Termination conditions and other parameters

Makefile                To compile everything
README                  This file
TODO.txt                Some things I have to do still
kmltest.cpp             kmltest source

Organization
------------
The various algorithms are invoked by kmltest, the main test driver.
This program inputs various parameters, inputs/generates data sets,
executes the appropriate algorithms, and prints statistics.

The program is organized around a set of classes.

KMpoint: (Files: KM_ANN.h, KM_ANN.cpp)
  There is no point "class".  A point is just a pointer to an array of
  doubles.  This is an inheritance of ANN, which uses this simple
  representation for its points.

  The typedefs KMdataPoint and KMcenter are just aliases for KMpoint,
  and are used as a hint for whether a point is used as a data or center
  point.

KMpointArray: (Files: KM_ANN.h, KM_ANN.cpp)
  A point array is a pointer to an array of KMpoint.  The typedefs
  KMdataArray and KMcenterArray are aliases for KMpointArray.

KMdata:  (Files: KMdata.h, KMdata.cpp)
  This class stores a set of data points.  It also has an associated
  member kcTree, which is a pointer to a kc tree for the point set (see
  below).  This class provides functions sampleCtr() and sampleCtrs()
  for sampling points to be used as centers.  These procedures just take
  a random sample of points, but it should be possible to extend this
  class so that more sophisticated sampling is possible (e.g., down the
  lines of what Matoushek does).

KCtree:  (Files: KCtree.h, KCtree.cpp, KCutil.h, KCutil.cpp)
  A kc tree class stores a enhanced form of a kd tree for a set of
  points.  In addition to storing the points, each node also contains
  the number of points, the centroid (actually the sum of coordinates)
  and the distortion of the point set relative to its centroid, and a
  bounding box for the point set.  Its constructor builds a tree from a
  set of points.  In addition it provides a procedure getNeighbors()
  which is used in Lloyd's algorithm for assigning points to their
  nearest neighbor among a set of k center points.

  These functions are a massively stripped-down version of the kd tree
  data structure of ANN.  The files KCutil.h and KCutil.cpp contain
  utility procedures used in the construction of the tree.

KMcenters: (Files: KMcenters.h, KMcenters.cpp)
  This class is used for storing a set of center points for a given data
  set.  It also contains a pointer to a KMdata object, which stores the
  associated data set.  It provides basic access functions, but not much
  more.

KMfilterCenters: (Files: KMfileterCenters.h, KMfilterCenters.cpp)
  This class extends the KMcenters class, and provides the main utility
  procedures for various k-means algorithms.  The most time-intensive
  aspect of k-means is assigning data points to their nearest center and
  computing distortions.  This class together with the kc tree makes use
  of a procedure, called filtering, for doing this.  See the file
  KMfilterCenters.h for more information as to how it works.

KMlocal: (Files: KMlocal.h, KMlocal.cpp)
  This class provides a generic k-means algorithm through local search.
  See the file KMlocal.h for an outline of the algorithm.  Basically it
  works by constructing an initial set of centers and then makes local
  modifications to this set.  There are two important extensions to this
  class:

  KMlocalLloyds: Repeatedly applies Lloyd's algorithm with randomly
        sampled starting points.
  KMlocalSwap: A local search heuristic, which works by performing swaps
        between existing centers and a set of candidate centers.
  KMlocalEZ_Hybrid: A simple hybrid algorithm, which does one swap
        followed by some number of iterations of Lloyd's.
  KMlocalHybrid: A more complex hybrid of Lloyd's and Swap, which performs
        some number of swaps followed by some number of iterations of
        Lloyd's algorithm.  To avoid getting trapped in local minima,
        an approach similar to simulated annealing is included as well.

KMterm: (Files: KMterm.h, KMterm.cpp)
  The algorithms described above are controlled by a number of different
  parameters.  These parameters are encapsulated in this class.  Among
  these are termination conditions, from which the class is named.

KMrand: (Files: KMrand.h, KMrand.cpp)
  This is not a class, but just a set of free-standing procedures, which
  are used for generating point sets according to various distributions.
