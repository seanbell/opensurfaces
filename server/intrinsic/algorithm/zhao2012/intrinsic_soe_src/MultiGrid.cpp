#include "MultiGrid.h"
#include <fstream>

//#define __DEBUG__

//
SparseMat restrictMat(int dim11, int dim12, int dim21, int dim22){
	//
	SparseMat rsp;
#ifdef __DEBUG__
	std::cout <<" dim11,dim12,dim21,dim22:" << dim11 << "," << dim12 << "," << dim21 << "," << dim22 << std::endl;
#endif
	rsp.reset(dim21 * dim22, dim11 * dim12);
	//
	double wMat[] = {
		0.0625,	0.125,	0.0625,
		0.125,	0.25,	0.125,
		0.0625,	0.125,	0.0625
	};

	for (int i = 0; i < dim21; i++)
	{
		for (int j = 0; j < dim22; j++)
		{
			int cxi = 2 * j;
			int cyi = 2 * i;
			//std::cout << "i,j:" << i << "," << j << std::endl;
			for (int k1 = -1; k1 <= 1; k1++)
			{
				for (int k2 = -1; k2 <= 1; k2++)
				{
					int cxj = cxi + k2;
					int cyj = cyi + k1;
					if (cxj < 0 || cxj >= dim12 || cyj < 0 || cyj >= dim11)
					{
						continue;
					}
					//
					rsp.addElement(i * dim22 + j, cyj * dim12 + cxj,wMat[(k1+1) * 3 + k2 + 1]);
				}
			}
		}
	}
	rsp.merge();
	return rsp;
}

SparseMat prolongMat(int dim11, int dim12, int dim21, int dim22){
	//
	double wMat[] = 
	{
		0.0625, 0.125, 0.0625,
		0.125, 0.25, 0.125,
		0.0625,0.125,0.0625
	};

	SparseMat psp;
	psp.reset(dim21 * dim22 , dim11 * dim12);

	for (int i = 0; i < dim11; i++)
	{
		for (int j = 0; j < dim12; j++)
		{
			//
			//std::cout << "i,j:" << i << "," << j << std::endl;
			int cxi = 2 * j;
			int cyi = 2 * i;

			for (int k1 = -1 ; k1 <= 1; k1++)
			{
				for (int k2 = -1; k2 <= 1; k2++)
				{
					int cxj = cxi + k2;
					int cyj = cyi + k1;
					if (cxj < 0 || cxj >= dim22 || cyj < 0 || cyj >= dim21)
					{
						continue;
					}
					psp.addElement(cyj * dim22 + cxj, i * dim12 + j, wMat[(k1+1) * 3 + k2 + 1]);
				}
			}
		}
	}
	//std::cout << "merge" << std::endl;
	psp.merge();
	return psp;
}


AMG::AMG(SparseMat& sp, db_vec& b,int dim1,int dim2,int level)
:m_origA(sp)
,m_origB(b)
,m_dim1(dim1)
,m_dim2(dim2)
,m_levelCnt(level){

	_buildStack();
}

void AMG::_buildStack(){
	//

}


void AMG::solve(){
}
