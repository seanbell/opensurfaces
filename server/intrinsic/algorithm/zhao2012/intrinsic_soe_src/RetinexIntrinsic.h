#ifndef __RETINEX_INTRINSIC__
#define __RETINEX_INTRINSIC__
#include "IntrinsicModel.h"


class RetinexIntrinsic:public IntrinsicModel{
public:
	ublas_cm_f m_retinexEnergyMat; //energy matrix
	float m_chromThrd;
	mat_f m_hWeight;
	mat_f m_vWeight;
public:
	RetinexIntrinsic(mat_3f img,float chromThrd = 0.001);
	void setChromThrd(float chromThrd){
		m_chromThrd = chromThrd;
	}
	~RetinexIntrinsic();
public:
	virtual void _solve();
	void addColorPlaneConstraint();
protected:
	mat_u _getClrEdgeMsk(int winSz = 3);
	virtual void _buildRetinexEnergyMat();
	virtual void _init();
	virtual void _albedoConstraint2SparseMat();
};

#endif