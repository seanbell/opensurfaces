/*
 * DirectSolver.cpp
 *
 *  Created on: Sep 26, 2010
 *      Author: zhaoqi
 */
#include "Timer.h"
#include "DirectSolver.h"

Solver::Solver() {
	// TODO Auto-generated constructor stub

}

Solver::~Solver() {
	// TODO Auto-generated destructor stub
}

//
//void UMFPACKSolver::solve(SparseMat& sm, db_vec& b, db_vec& x){
//	//
//	//get the ccs vectors
//	taucs_sp& tsp = sm.m_taucsMat;
//	int status,n, m ;
//	m = sm.m_dim1;
//	n = sm.m_dim2;
//	int* Ap = &(tsp.m_colIdx[0]);
//	int* Ai = &(tsp.m_rowIdx[0]);
//	double* Ax = &(tsp.m_val[0]);
//	double* X = new double[b.size()];
//	double* B = new double[b.size()];
//	for(unsigned int i = 0; i < b.size(); i++){
//		B[i] = b[i];
//	}
//	double Control [UMFPACK_CONTROL], Info [UMFPACK_INFO];
//	void *Symbolic, *Numeric ;
//	Timer timer;
//	timer.start();
//	umfpack_di_defaults (Control);
//	status = umfpack_di_symbolic (m, n, Ap, Ai, Ax, &Symbolic, Control, Info) ;
//	status = umfpack_di_numeric (Ap, Ai, Ax, Symbolic, &Numeric, Control, Info) ;
//	status = umfpack_di_solve (UMFPACK_A, Ap, Ai, Ax, X, B, Numeric, Control, Info) ;
//	timer.stop();
//	std::cout << timer.getElapse() << " seconds elapsed" << std::endl;
//	umfpack_di_free_symbolic (&Symbolic) ;
//	umfpack_di_free_numeric (&Numeric) ;
//	//copy X to xvec
//	for(unsigned int i = 0; i < b.size(); i++){
//		x[i] = X[i];
//	}
//	//
//}

void SLSolver::solve(SparseMat& sm,db_vec& b,db_vec& x){
	//using iterative method to solve Sm*x = b
//	taucs_sp& tsp = sm.m_taucsMat;
//	int nnz = tsp.m_val.size();
//	CompCol_Mat_double A(sm.m_dim1,sm.m_dim2,nnz,&(tsp.m_val[0]),&(tsp.m_rowIdx[0]),&(tsp.m_colIdx[0]));
//	VECTOR_double b1(b.size(),0);
//	VECTOR_double x1(b.size(),0);
//	for(unsigned int i = 0; i < b.size(); i++)
//		b1[i] = b[i];
//	for(unsigned int i = 0; i < b.size(); i++)
//		x[i] = x1[i];
}
