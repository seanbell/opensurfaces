#ifndef __NORMAL_ESTIMATOR_H__
#define __NORMAL_ESTIMATOR_H__

#include <ANN/ANN.h>
#include "cv_header.h"
#include "structDef.h"

class NormalEstimator
{
public:
	std::vector<cv::Vec3f> m_pt;
	std::vector<cv::Vec3f> m_ptNorm;
	std::vector<bool> m_ptNormFlag;
public:
	NormalEstimator(std::vector<cv::Vec3f> pt = std::vector<cv::Vec3f>());
	static void computePCA(cv::Mat& oVec, cv::Mat& eVec,cv::Mat& valVec);
	void specifyPointSet(std::vector<cv::Vec3f>& pt);
	virtual void fitNormal();
	virtual ~NormalEstimator();
};

#endif
