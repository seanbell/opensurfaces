#include "SparseMat.h"
#include <algorithm>
#include <fstream>
#include <iostream>
#include <math.h>
#include "Matlab.h"

#define __MATLAB_SP_PROD__

SparseMat::SparseMat(int dim1,int dim2)
{
	reset(dim1,dim2);
}

void SparseMat::reset(int dim1, int dim2){
	//
	m_dim1 = dim1;
	m_dim2 = dim2;
	m_mergeDone = false;
	m_crs.clear();
	m_ccs.clear();
	m_crs.assign(m_dim1,Slot());
	m_ccs.assign(m_dim2,Slot());
	//
}

void SparseMat::addElement(int rIdx, int cIdx, double val){
	m_crs[rIdx].push_back(IdxVal(cIdx,val));
	m_ccs[cIdx].push_back(IdxVal(rIdx,val));
}


void SparseMat::_mergeSlot(Slot& st){
	//merge elements in slot with the same index
	if (st.empty())
	{
		return;
	}

	std::sort(st.begin(),st.end());
	//merge elements with identical column index
	std::vector<IdxVal> newSlot;
	//
	int lastIdx = -1;
	double sum = 0.0f;
	for (int j = 0; j < st.size(); j++)
	{
		IdxVal& re = st[j];
		if(re.m_idx != lastIdx){
			//encounter an new idx, save previous result
			if (lastIdx >= 0)
			{
				newSlot.push_back(IdxVal(lastIdx,sum));
			}
			sum = re.m_val;
			lastIdx = re.m_idx;
		}
		else{
			sum += re.m_val;
		}
	}
	if (lastIdx >= 0)
	{
		newSlot.push_back(IdxVal(lastIdx,sum));
	}
	//
	st = newSlot;
}
void SparseMat::merge(){

	int nnz = 0;
	for (int i = 0; i < m_dim1; i++)
	{
		std::vector<IdxVal>& tmpRow = m_crs[i];
		if (tmpRow.empty())
		{
			continue;
		}
		_mergeSlot(tmpRow);
		nnz += tmpRow.size();
	}
	//
	for (int i = 0; i < m_dim2; i++)
	{
		std::vector<IdxVal>& tmpCol= m_ccs[i];
		if (tmpCol.empty())
		{
			continue;
		}
		_mergeSlot(tmpCol);
	}
	m_mergeDone = true;
	//now create a taucs sparse matrix
	m_taucsMat.reset();
	m_taucsMat.m_colIdx.assign(m_dim2 + 1,0);
	m_taucsMat.m_rowIdx.assign(nnz,0);
	m_taucsMat.m_val.assign(nnz,0);
	int cnt = 0;
	for (int i = 0; i < m_ccs.size(); i++)
	{
		Slot& tmpCol = m_ccs[i];
		int colCnt = 0;
		for (int j = 0; j < tmpCol.size(); j++)
		{
			if (tmpCol[j].m_idx < i)
			{
				continue;
			}
			m_taucsMat.m_rowIdx[cnt] = tmpCol[j].m_idx;
			m_taucsMat.m_val[cnt] = tmpCol[j].m_val;
			cnt++;
			colCnt++;
		}
		m_taucsMat.m_colIdx[i + 1] = m_taucsMat.m_colIdx[i] + colCnt;
	}
	m_taucsMat.m_colIdx.resize(m_taucsMat.m_colIdx.size());
	m_taucsMat.m_rowIdx.resize(m_taucsMat.m_rowIdx.size());
	m_taucsMat.m_val.resize(m_taucsMat.m_val.size());
	//done
}

Slot& SparseMat::getRow(int rIdx){
	return m_crs[rIdx];
}

Slot& SparseMat::getCol(int rIdx){
	//
	return m_ccs[rIdx];
}

void SparseMat::dumpToFile(std::string filePath ){
	//dump the matrix to the file
	std::ofstream ofs;
	ofs.open(filePath.c_str(),std::ios::out);
	if (!ofs.good())
	{
		std::cout << "failed to open the file" << std::endl;
		return;
	}

	for(int i = 0; i < m_crs.size(); i++){
		std::vector<IdxVal>& tmpRow = m_crs[i];
		if (tmpRow.empty())
		{
			continue;
		}
		for (int j = 0; j < tmpRow.size(); j++)
		{
			IdxVal& re = tmpRow[j];
			ofs << i << " " << re.m_idx << " " << re.m_val << "\n";
		}
		//
	}
	ofs.close();
}


SparseMat::~SparseMat(){
}

//////////////////////////////////////////////////////////////////////////
//some vector routines

inline double dotProd(double* v1, double* v2, int dim){
	double sum = 0;
	for (int i = 0; i < dim; i++)
	{
		sum += (v1[i] * v2[i]);
	}
	return sum;
}

inline void vecSub(double* v1, double* v2, int dim){
	for (int i = 0; i < dim; i++)
	{
		v1[i] -= v2[i];
	}
	//
}

inline void vecAdd(double* v1, double* v2, int dim){
	for (int i = 0; i < dim; i++)
	{
		v1[i] += v2[i];
	}
	//
}

inline void scaleProd(double* v, double scale, int dim){
	for (int i = 0; i < dim; i++)
	{
		v[i] *= scale;
	}
}

inline void scaleAdd(double* v1, double* v2, double scale,int dim){
	for (int i = 0; i < dim; i++)
	{
		v1[i] += (scale * v2[i]);
	}
}



void printVec(double* vec, int dim){
	for (int i = 0; i < dim; i++)
	{
		std::cout << vec[i] << std::endl;
	}
}


double operator* ( Slot& s1, Slot& s2){
	//s1 and s2 are sparse structure
	//the complexity would be O(L1+L2) where L1 and L2 are Slot's size respectively
	int i = 0, j = 0;
	double prod = 0.0f;
	//std::cout << s1.size() << "," << s2.size() << std::endl;

	for (i = 0; i < s1.size() && j < s2.size(); i++)
	{
		//
		for (; j < s2.size(); j++){
			if (s2[j].m_idx >= s1[i].m_idx)
			{
				break;
			}
		}
		if (j == s2.size())
		{
			break;
		}
		if (s2[j].m_idx > s1[i].m_idx)
		{
			continue;
		}
		//std::cout << "i,j:" << s1[i].m_idx << "," << s2[j].m_idx << std::endl;
		//
		prod += (s1[i].m_val * s2[j].m_val);
	}
	return prod;
}


db_vec operator* ( SparseMat& sp,  db_vec& v){
	//
	if (sp.m_dim2 != v.size())
	{
		std::cout << "matrix vector size does not match" << std::endl;
		return db_vec();
	}
	//
	db_vec resVec(sp.m_dim1);
#ifdef __MATLAB_SP_PROD__
	MatLab::ref().spmVecProd(sp,v,resVec);
#else
	for (int i = 0; i < sp.m_dim1; i++)
	{
		Slot& tmpRow = sp.getRow(i);
		double sum = 0.0f;
		for (int j = 0; j < tmpRow.size(); j++)
		{

			sum += (tmpRow[j].m_val * v[tmpRow[j].m_idx]);
		}
		resVec[i] = sum;
	}
#endif
	return resVec;
}



void testSPM(){
	//
	SparseMat sp1;
	sp1.reset(3,3);
	sp1.addElement(0,0,1);
	sp1.addElement(0,2,1);
	sp1.addElement(1,0,2);
	sp1.addElement(1,1,1);
	sp1.addElement(1,2,3);
	sp1.addElement(2,2,5);
	sp1.merge();
	std::cout << sp1 << std::endl;

	db_vec vec;
	vec.push_back(1);
	vec.push_back(2);
	vec.push_back(3);

	db_vec resv = sp1 * vec;

	for (int i = 0; i < resv.size(); i++)
	{
		std::cout << resv[i] << std::endl;
	}

	//SparseMat r = sp1 * sp1;
	//std::cout << r << std::endl;
	//int idx[] = {0,2,5,10};
	//int idx1[] = {1,2,5,6};

	//double val[] ={1,2,3,4};
	//Slot st1,st2;
	//for (int i = 0; i < 4; i++)
	//{
	//	st1.push_back(IdxVal(idx[i],val[i]));
	//	st2.push_back(IdxVal(idx1[i],val[i]));
	//}
	//double prod = st1 * st2;
	//std::cout << "prod:" << prod << std::endl;
}
#define  __IJV__

std::ostream& operator<< (std::ostream& oss, const SparseMat& sp){
#ifdef  __IJV__
	for (int i = 0; i < sp.m_dim1; i++)
	{
		const Slot& slot = sp.getRow(i);
		if (slot.empty())
		{
			continue;
		}
		for (int j = 0; j < slot.size(); j++)
		{
			oss << i << " " << slot[j].m_idx << " " << slot[j].m_val << std::endl;
		}
	}
#else
	for (int i = 0; i < sp.m_dim1; i++)
	{

		const Slot& slot = sp.getRow(i);
		if (slot.empty())
		{
			continue;
		}
		oss << "row " << i << " :" ;
		for (int j = 0; j < slot.size(); j++ )
		{
			oss << slot[j].m_val << " ";
		}
		oss << std::endl;
	}

#endif
	return oss;
}



SparseMat operator* ( SparseMat& sp1,  SparseMat& sp2){
	//O(n^3) computational complexity
	//row * column
	SparseMat resultSP;
#ifdef __MATLAB_SP_PROD__
	MatLab::ref().spmspmProd(sp1,sp2,resultSP);
#else
	int dim1 = sp1.m_dim1;
	int dim2 = sp2.m_dim2;
	resultSP.reset(dim1,dim2);

	for (int i = 0; i < dim1; i++)
	{
		//
		//std::cout << "i:" << i << std::endl;
		Slot& tmpRow = sp1.getRow(i);
		for (int j = 0; j < dim2; j++)
		{
			Slot& tmpCol = sp2.getCol(j);
			//product

			double prod = tmpRow * tmpCol;
			if (prod > 0) //non-zero element
			{
				resultSP.addElement(i,j,prod);
			}
		}
	}
	resultSP.merge(); //
#endif

	return resultSP;
}