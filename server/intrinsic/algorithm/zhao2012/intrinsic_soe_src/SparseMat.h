#ifndef __MY_SP__
#define __MY_SP__
#include <vector>
#include "ublas.h"
#include <iostream>


typedef std::vector<double> db_vec;

struct IdxVal{
	int m_idx;
	double m_val;
	IdxVal(int idx = -1,double val = 0.0f)
		:m_idx(idx),m_val(val){}
	inline bool operator< (const IdxVal& re2) const {
		return m_idx < re2.m_idx;
	}
};


typedef std::vector<IdxVal> Slot;

struct taucs_sp{
	//
	std::vector<int> m_colIdx;
	std::vector<int> m_rowIdx;
	std::vector<double> m_val;
	void reset(){
		m_colIdx.clear();
		m_rowIdx.clear();
		m_val.clear();
	}
};

class SparseMat
{
public:
	int m_dim1,m_dim2;
	std::vector<Slot> m_crs;
	std::vector<Slot> m_ccs;
	void _mergeSlot(Slot& st);
	taucs_sp m_taucsMat;
	bool m_mergeDone;
public:
	SparseMat(int dim1 = 0,int dim2 = 0);
	void reset(int dim1, int dim2);
	void addElement(int rIdx, int cIdx, double val);
	void merge();
	void dumpToFile(std::string filePath = "");
	Slot& getRow(int rIdx);
	const Slot& getRow(int idx) const{
		return m_crs[idx];
	}
	Slot& getCol(int cIdx);
	const Slot& getCol(int cIdx) const{
		return m_ccs[cIdx];
	}

	virtual ~SparseMat();
};


std::ostream& operator<< (std::ostream& oss, const SparseMat& sp);


double operator* ( Slot& s1,  Slot& s2);
db_vec operator* ( SparseMat& sp,  db_vec& v);
SparseMat operator* ( SparseMat& sp1,  SparseMat& sp2);

void testCG();
void testSPM();

#endif
