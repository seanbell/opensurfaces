#include "RefGS.h"
#include "structDef.h"
#include "fw_header.h"
#include <ANN/ANN.h>
class FLANNAdapt{
protected:
	cv::flann::KDTreeIndexParams m_indexParam;
	cv::flann::SearchParams m_searchParam;
	mat_f m_dataPts;
	cv::flann::Index* m_indexerPtr;
public:
	FLANNAdapt(ANNpointArray dataPts, int ptCnt, int dim);
	int annkFRSearch(ANNpoint queryPt, float trd_dist, int nPts, ANNidxArray nnIdx, ANNdistArray dists, float epsilon);
	virtual ~FLANNAdapt();
};

