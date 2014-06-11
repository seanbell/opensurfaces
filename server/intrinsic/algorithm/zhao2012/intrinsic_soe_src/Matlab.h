#ifndef __MATLAB_H__
#define __MATLAB_H__
#include <engine.h>
#include "ublas.h"
#include "structDef.h"
#include <opencv/cxcore.h>
#include "SparseMat.h"
class MatLab{
protected:
	Engine* m_pEngine;
	MatLab()
	{
		m_pEngine = engOpen("matlab -nosplash -nodisplay");
		m_linSolveTime = 0;
		m_matrixTime = 0;
		if(!m_pEngine)
			std::cout << "Failed to connect to matlab server" << std::endl;
	};
public:
	double m_linSolveTime;
	double m_matrixTime;
public:
	static MatLab& ref(){
		static MatLab ml;
		return ml;
	}
	Engine* getEngPtr(){
		return m_pEngine;
	}
	void putSparseMatrix(SparseMat& tcm,char* matVarName);
	void putSparseMatrix(ublas_cm_f& sm, char* matVarName);
	void putVec(db_vec& vec,char* matVarName);
	void putVec(ublas_vec_f& vec,char* matVarName);
	db_vec sparseLinSolve(SparseMat& sm,db_vec& b);
	void spmVecProd(SparseMat& sp,db_vec& vec, db_vec& vec1);
	void spmspmProd(SparseMat& sp1, SparseMat& sp2,SparseMat& rsp);
	ublas_vec_f sparseLinSolve(ublas_cm_f& sm, ublas_vec_f& b);
	ublas_vec_f sparseLinSolve(SparseMat& sm, ublas_vec_f& b);
	void evalCmd(std::string cmd);
	ublas_vec_f getVec(std::string varName,int sz);
	mat_3f getImage(std::string varName,int h,int w);
	~MatLab(){
		if(m_pEngine)
		engClose(m_pEngine);
	}
};
#endif
