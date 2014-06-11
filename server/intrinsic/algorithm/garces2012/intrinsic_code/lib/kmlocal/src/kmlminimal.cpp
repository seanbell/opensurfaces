//----------------------------------------------------------------------
//      File:           kmlminimal.cpp
//      Programmer:     David Mount
//      Last modified:  05/14/04
//      Description:    Minimal sample program for kmeans
//----------------------------------------------------------------------
// Copyright (C) 2004-2005 David M. Mount and University of Maryland
// All Rights Reserved.
// 
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or (at
// your option) any later version.  See the file Copyright.txt in the
// main directory.
// 
// The University of Maryland and the authors make no representations
// about the suitability or fitness of this software for any purpose.
// It is provided "as is" without express or implied warranty.
//----------------------------------------------------------------------

#include <cstdlib>			// C standard includes
#include <iostream>			// C++ I/O
#include <string>			// C++ strings
#include "KMlocal.h"			// k-means algorithms

using namespace std;			// make std:: available

// execution parameters (see KMterm.h and KMlocal.h)
KMterm  term(100, 0, 0, 0,              // run for 100 stages
             0.10, 0.10, 3,             // other typical parameter values 
             0.50, 10, 0.95);

int main(int argc, char **argv)
{
    int		k	= 4;			// number of centers
    int		dim	= 2;			// dimension
    int		nPts	= 20;			// number of data points

    KMdata dataPts(dim, nPts);			// allocate data storage
    kmUniformPts(dataPts.getPts(), nPts, dim);	// generate random points
    dataPts.buildKcTree();			// build filtering structure
    KMfilterCenters ctrs(k, dataPts);		// allocate centers

    						// run the algorithm
    KMlocalLloyds       kmAlg(ctrs, term);	// repeated Lloyd's
    // KMlocalSwap      kmAlg(ctrs, term);	// Swap heuristic
    // KMlocalEZ_Hybrid kmAlg(ctrs, term);	// EZ-Hybrid heuristic
    // KMlocalHybrid    kmAlg(ctrs, term);	// Hybrid heuristic
    ctrs = kmAlg.execute();			// execute
    						// print number of stages
    cout << "Number of stages: " << kmAlg.getTotalStages() << "\n";
						// print average distortion
    cout << "Average distortion: " << ctrs.getDist()/nPts << "\n";
    ctrs.print();				// print final centers

    kmExit(0);
}
