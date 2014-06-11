#include "ANNCluster.h"

ANNCluster::ANNCluster() {
	
}

void ANNCluster::doCluster(mat_f& data, grpEle_vect& grpVect, float radius) {
	//
	
	int ptCnt = data.size().height;
	int dim = data.size().width;
	//this is ANN implementation, but it is changed to FLANN now, please refer the updated block below
	float *ptWeight = new float[ptCnt];
	std::vector<bool> mFlag(ptCnt,false);

#ifdef __USE_ANN__
	ANNpointArray ptArray = annAllocPts(ptCnt, dim);
	//assign point values
	for (int i=0; i<ptCnt; i++) {
		ANNpoint ptPtr = ptArray[i];
		for(int j = 0; j < dim; j++){
			float tmp = data(i,j);
			ptPtr[j] = data(i , j);			
		}
	}
	///
	ANNkd_tree kdt(ptArray, ptCnt, dim);
	ANNpoint queryPt = annAllocPt(dim); 
	ANNidxArray nnIdx = new ANNidx[ptCnt];
	ANNdistArray nnDist = new ANNdist[ptCnt];
	int grpCounter = 0;
	for (int i=0; i<ptCnt; i++) {
		if(mFlag[i])
			continue; //skip matched point
		for(int j = 0; j < dim; j++){
			queryPt[j] = data(i,j);
		}
		
		int resultCnt = kdt.annkFRSearch(queryPt, radius, ptCnt, nnIdx, nnDist);
		std::vector<cv::Vec3f> nnPt;
		GrpEle ge;
		ge.m_gID = grpCounter++ ;
		for (int j=0; j < resultCnt; j++) {
			ANNidx idx = nnIdx[j];
			mFlag[idx] = true;
			ANNpoint tmpNNPt = ptArray[idx];
			cv::Vec3f cvPt(tmpNNPt[0], tmpNNPt[1], tmpNNPt[2]);
			ptWeight[j] = exp(-nnDist[j]/radius);
			ge.m_eMember.push_back(Element(idx,ptWeight[j]));
		}
		grpVect.push_back(ge);
	}
	annDeallocPt(queryPt);
	annDeallocPts(ptArray);
	delete [] nnDist;
	delete [] nnIdx;
	delete [] ptWeight;
#else
	cv::flann::KDTreeIndexParams idxParams(4);
	cv::flann::SearchParams scParams(32);
	cv::flann::Index indexer(data,idxParams);
	std::vector<float> nnDists(dim);
	std::vector<int> nnInds(dim);
	std::vector<float> queryPt(dim);
	for(int i = 0; i < ptCnt; i++){
		if(mFlag[i])
			continue;
		for(int j = 0; j < dim; j++)
			queryPt[j] = data(i,j);
		int nnCnt = indexer.radiusSearch(queryPt,nnInds,nnDists,radius,scParams);
		GrpEle ge;
		for(int k = 0; k < nnCnt; k++){
			int tmpIdx = nnInds[k];
			float tmpDist = nnDists[k];
			float tmpWeight = exp(-tmpDist/radius);
			ge.m_eMember.push_back(Element(tmpIdx,tmpWeight));
		}
		grpVect.push_back(ge);
	}
#endif
}

ANNCluster::~ANNCluster() {
}
