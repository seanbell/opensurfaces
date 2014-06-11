#include "NormalEstimator.h"
#include <fstream>

NormalEstimator::NormalEstimator(std::vector<cv::Vec3f> pt)
{
	specifyPointSet(pt);
}



void NormalEstimator::computePCA(cv::Mat& oVec, cv::Mat& eVec,cv::Mat& valVec){
	//
	int dim = oVec.size().width;
	int oCnt = oVec.size().height;
	eVec = cv::Mat(dim,dim,CV_64FC1);
	valVec = cv::Mat(dim,1,CV_64FC1);

	//compute the mean
	cv::Mat row(1,dim,CV_64FC1);
	row = 0.0f;
	for (int i = 0; i < oCnt; i++)
	{
		row = row + oVec.row(i);
	}
	row /= oCnt;
	//for (int i = 0; i < dim; i++)
	//{
	//	std::cout << row.at<double>(0,i) << " " ;
	//}
	//std::cout << std::endl;
	//getchar();
	//subtraction
	for (int i = 0; i < oCnt; i++)
	{
		for (int j = 0; j < dim; j++)
		{
			oVec.at<double>(i,j) = oVec.at<double>(i,j) - row.at<double>(0,j);
		}
	}
	//
	cv::Mat extProd(dim,dim,CV_64FC1);
	extProd = 0.0f;

	cv::Mat oVecT(dim,1,CV_64FC1);

	//for (int i = 0; i < oCnt; i++)
	//{
	//	for (int j = 0; j < dim; j++)
	//	{
	//		std::cout << oVec.at<double>(i,j) << " ";
	//	}
	//	std::cout << std::endl;
	//}
	//getchar();

	for (int i = 0; i < oCnt; i++)
	{
		cv::transpose(oVec.row(i),oVecT);
		extProd = extProd +  (oVecT * oVec.row(i));
		////print the product
		//for (int i1 = 0; i1 < dim ;i1++)
		//{
		//	for (int j1 = 0; j1 < dim; j1++)
		//	{
		//		std::cout << tmp.at<double>(i1,j1) << " ";
		//	}
		//	std::cout << std::endl;
		//}
		//getchar();

	}
	extProd /= oCnt;
	//for (int i = 0; i < dim ;i++)
	//{
	//	for (int j = 0; j < dim; j++)
	//	{
	//		std::cout << extProd.at<double>(i,j) << " ";
	//	}
	//	std::cout << std::endl;
	//}
	//getchar();
	cv::eigen(extProd,valVec,eVec);
	//

}

void NormalEstimator::specifyPointSet(std::vector<cv::Vec3f>& pt){
	//
	m_pt = pt;
	m_ptNorm.insert(m_ptNorm.begin(),m_pt.size(),cv::Vec3f(0,0,0));
	m_ptNormFlag.insert(m_ptNormFlag.begin(),m_pt.size(),false);
}


void NormalEstimator::fitNormal(){
	//
	//compute surface normal
	int ptCnt = m_pt.size();
	if (ptCnt <= 0)
	{
		std::cout << "no point set provided" << std::endl;
		return;
	}
	ANNpointArray ptArray = annAllocPts(ptCnt, 3);
	//assign point values
	for (int i=0; i<ptCnt; i++) {
		cv::Vec3f pt = m_pt[i];
		ANNpoint ptPtr = ptArray[i];
		ptPtr[0] = pt[0];
		ptPtr[1] = pt[1];
		ptPtr[2] = pt[2];
	}

	///
	ANNkd_tree kdt(ptArray, ptCnt, 3);
	
	ANNpoint queryPt = annAllocPt(3);
	int nnCnt = 100;

	ANNidxArray nnIdx = new ANNidx[nnCnt];
	ANNdistArray nnDist = new ANNdist[nnCnt];

	float sigma = -1;
	float evalRatio = 0.05;
	//estimate sigma
	for (int i=0; i < ptCnt; i++) {
		cv::Vec3f pt = m_pt[i];
		queryPt[0] = pt[0];
		queryPt[1] = pt[1];
		queryPt[2] = pt[2];

		//kdt.annkSearch(queryPt,nnCnt, nnIdx, nnDist);
		kdt.annkSearch(queryPt,50, nnIdx, nnDist);
		if (nnDist[49] < sigma ||sigma == -1 )
		{
			sigma = nnDist[49];
		}
	}
	sigma = 0.001;
	std::cout << "search radius:" << sigma << std::endl;
	std::cout << "estimating normals for point set by PCA, be patient..." << std::endl;
	for (int i=0; i < ptCnt; i++) {
		cv::Vec3f pt = m_pt[i];
		queryPt[0] = pt[0];
		queryPt[1] = pt[1];
		queryPt[2] = pt[2];

		//kdt.annkSearch(queryPt,nnCnt, nnIdx, nnDist);
		kdt.annkFRSearch(queryPt, sigma, nnCnt, nnIdx, nnDist);
		int validCnt = 0;
		for (int j = 0; j < nnCnt; j++)
		{
			if (nnIdx[j] == ANN_NULL_IDX)
			{
				break;
			}
			validCnt++;
		}
		//std::cout << validCnt << std::endl;
		if (validCnt < 3)
		{
			continue;
		}
		
		cv::Mat pcaVec(validCnt,3,CV_64FC1);
		cv::Mat pcaMean(1,3,CV_64FC1);
		for (int j = 0; j < validCnt; j++)
		{
			pcaVec.at<double>(j,0) = m_pt[nnIdx[j]][0];
			pcaVec.at<double>(j,1) = m_pt[nnIdx[j]][1];
			pcaVec.at<double>(j,2) = m_pt[nnIdx[j]][2];
		}
		cv::PCA pca(pcaVec,cv::Mat(),CV_PCA_DATA_AS_ROW);

		if (pca.eigenvalues.at<double>(2,0) / pca.eigenvalues.at<double>(1,0) > evalRatio)
		{
			continue;
		}

		m_ptNorm[i] = cv::Vec3f(pca.eigenvectors.at<double>(2,0),pca.eigenvectors.at<double>(2,1),pca.eigenvectors.at<double>(2,2));
		float nr = cv::norm(m_ptNorm[i]);
		m_ptNorm[i][0] /= nr;
		m_ptNorm[i][1] /= nr;
		m_ptNorm[i][2] /= nr;
		//std::cout << m_ptNorm[i][0] << " " << m_ptNorm[i][1] << " " << m_ptNorm[i][2] << std::endl;
		m_ptNormFlag[i] = true;

	}

	//
	std::cout << "done..." << std::endl;
//////////////////////////////////////////////////////////////////////////

	//std::cout << "correct normal direction..." << std::endl;
	//sigma *= 1; //
	//nnCnt *= 1; //
	////reallocate the space for nn idx and nn dist array
	//delete [] nnDist;
	//delete [] nnIdx;
	//nnIdx = new ANNidx[nnCnt];
	//nnDist = new ANNdist[nnCnt];

	//int invertCnt = 0;
	//for (int i = 0; i < ptCnt; i++)
	//{
	//	if (!m_ptNormFlag[i])
	//	{
	//		continue;
	//	}
	//	
	//	cv::Vec3f pt = m_pt[i];
	//	queryPt[0] = pt[0];
	//	queryPt[1] = pt[1];
	//	queryPt[2] = pt[2];

	//	kdt.annkFRSearch(queryPt, sigma, nnCnt, nnIdx, nnDist);
	//	int validCnt = 0, normConsCnt = 0, distConsCnt = 0;
	//	for (int j = 0; j < nnCnt; j++)
	//	{
	//		if (nnIdx[j] == ANN_NULL_IDX)
	//		{
	//			break;
	//		}
	//		else{
	//			//check the direction
	//			cv::Vec3f v1 = m_ptNorm[i];
	//			cv::Vec3f v2 = m_ptNorm[nnIdx[j]];
	//			
	//			if (!m_ptNormFlag[nnIdx[j]])
	//			{
	//				continue;
	//			}else{
	//				//
	//				validCnt++;
	//				if( v2.ddot(v1) > 0 )
	//					normConsCnt++;
	//			}
	//		}
	//	}
	//	//inconsistency detected, invert the direction
	//	if (normConsCnt / validCnt < 0.9)
	//	{
	//		//std::cout << "invert" << std::endl;
	//		invertCnt++;
	//		m_ptNorm[i] = cv::Vec3f(0,0,0) - m_ptNorm[i];
	//	}
	//}
	//std::cout << "# of inverted vertex:" << invertCnt << std::endl;
	////////////////////////////////////////////////////////////////////////////
	
	annDeallocPt(queryPt);
	annDeallocPts(ptArray);
	delete [] nnDist;
	delete [] nnIdx;

}
NormalEstimator::~NormalEstimator(){

}
