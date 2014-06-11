/*
 * DirectSolver.h
 *
 *  Created on: Sep 26, 2010
 *      Author: zhaoqi
 */

#ifndef DIRECTSOLVER_H_
#define DIRECTSOLVER_H_
#include "SparseMat.h"

class Solver {
public:
	Solver();
	virtual void solve(SparseMat& sm, db_vec& b, db_vec& x) = 0;
	virtual ~Solver();
};


//class UMFPACKSolver: public Solver{
//public:
//	virtual void solve(SparseMat& sm, db_vec& b, db_vec& x);
//};


class SLSolver: public Solver{
public:
	virtual void solve(SparseMat& sm, db_vec& b, db_vec& x);
};
#endif /* DIRECTSOLVER_H_ */
