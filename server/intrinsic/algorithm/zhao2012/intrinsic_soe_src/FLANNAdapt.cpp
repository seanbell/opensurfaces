#include "FLANNAdapt.h"

FLANNAdapt::FLANNAdapt(ANNpointArray dataPts, int ptCnt, int dim)
	:
	m_indexParam(4),
	m_searchParam(32),
	m_dataPts(ptCnt,dim),
	m_indexerPtr(new cv::flann::Index(m_dataPts,m_indexParam))
{
	//
	//m_indexerPtr = new cv::flann::Index(m_dataPts,m_indexParam);

}

int FLANNAdapt::annkFRSearch(ANNpoint queryPt, float trd_dist, int nPts, ANNidxArray nnIdx, ANNdistArray dists, float epsilon){
	//
	int dim = m_dataPts.size().width;
	std::vector<float> qPoint(dim,0);
	std::vector<int> nnIdxArray(nPts);
	std::vector<float> nnDistArray(nPts);
	//make data copy
	for(int i = 0; i < dim; qPoint[i]=queryPt[i++]);
	int nnCnt = m_indexerPtr->radiusSearch(qPoint,nnIdxArray,nnDistArray,trd_dist,m_searchParam);
	for(int i = 0; i < nnCnt;i++){
		nnIdx[i] = nnIdxArray[i];
		dists[i] = nnDistArray[i];
	}
	return nnCnt;
}

FLANNAdapt::~FLANNAdapt(){
	if(m_indexerPtr)
		delete m_indexerPtr;
}
