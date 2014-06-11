#ifndef __MULTI_GRID__
#define __MULTI_GRID__

#include "SparseMat.h"

SparseMat restrictMat(int dim11, int dim12, int dim21, int dim22);
SparseMat prolongMat(int dim11, int dim12, int dim21, int dim22);


class AMG{
protected:
	SparseMat m_origA;
	db_vec m_origB;
	std::vector<SparseMat> m_aMatStack;
	std::vector<SparseMat> m_pHStack;
	std::vector<SparseMat> m_rHStack;
	std::vector<db_vec> m_bVecStack;
	std::vector<db_vec> m_xVecStack;
	std::vector<int> m_dim1Stack;
	std::vector<int> m_dim2Stack;
	int m_dim1;
	int m_dim2;
	int m_levelCnt;

protected:
	void _buildStack();
public:
	AMG(SparseMat& sp, db_vec& b,int dim1,int dim2,int level);
	db_vec& getSolution(){
		return m_xVecStack[0];
	}
	void solve();
};


#endif
