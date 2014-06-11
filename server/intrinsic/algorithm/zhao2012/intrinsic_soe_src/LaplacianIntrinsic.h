#ifndef __LAPLACIAN_INTRINSIC__
#define __LAPLACIAN_INTRINSIC__
#include "IntrinsicModel.h"

class LaplacianIntrinsic:public IntrinsicModel{
protected:
	virtual void _init();
	void _buildLMat();
	virtual void _albedoConstraint2SparseMat() ;
public:
	LaplacianIntrinsic(mat_3f img,int lWinSize);
	void lMat2sLmat();
	virtual void _solve();
	ublas_vec_f GSOptimize( ublas_vec_f& u0, int iterCnt, float m_lambdaConstrain,float epsilon);
	~LaplacianIntrinsic(){}
};
#endif