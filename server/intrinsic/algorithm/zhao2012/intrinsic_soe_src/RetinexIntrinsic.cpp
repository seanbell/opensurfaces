#include "RetinexIntrinsic.h"


RetinexIntrinsic::RetinexIntrinsic(mat_3f img,float chromThrd)
:IntrinsicModel(img,"RI")
,m_chromThrd(chromThrd){
	m_hWeight = mat_f(img.size());
	m_hWeight = mat_f(img.size());
}

float computeVectorVar(std::vector<cv::Vec3f>& pts){
	//
	if (pts.empty())
	{
		return -1;
	}
	cv::Vec3f avgVec(0,0,0);
	for (int i = 0; i < pts.size(); i++)
	{
		avgVec += pts[i];
	}
	avgVec[0] /= pts.size();
	avgVec[1] /= pts.size();
	avgVec[2] /= pts.size();
	float var = 0.0f;

	for (int i = 0; i < pts.size(); i++)

	{
		float tmp = cv::norm(pts[i] - avgVec);
		var += (tmp * tmp);
	}
	return sqrt(var / pts.size());
}

mat_u RetinexIntrinsic::_getClrEdgeMsk(int winSz ){

	//locating the color edge by computing the color variance of local window
	//mat_3f img = m_img.clone();
	mat_3f img = m_dm.getChrom().clone();
	int ih = img.size().height;
	int iw = img.size().width;
	int hSz = winSz >> 1;

	float varThrd = 0.02;

	mat_u msk(ih,iw);
	msk = 0;

	for (int i = hSz; i < ih - hSz; i++)
	{
		for (int j = hSz; j < iw - hSz; j++)
		{
			std::vector<cv::Vec3f> pts;
			for (int k1 = -hSz; k1 <= hSz; k1++)
			{
				for (int k2 = -hSz; k2 <= hSz; k2++)
				{
					int px = j + k2;
					int py = i + k1;
					pts.push_back(img(py,px));
				}
			}
			//compute the variance
			float tmpVar = computeVectorVar(pts);
			if (tmpVar >= varThrd)
			{
				msk(i,j) = 255;
			}
		}
	}
	return msk;
}

void RetinexIntrinsic::_buildRetinexEnergyMat(){
	//
	float trd = m_chromThrd;
	std::cout << "build the retinex constraint matrix......" << std::endl;
	int ih = m_img.size().height;
	int iw = m_img.size().width;
	int pixelCnt = iw * ih;
	m_retinexEnergyMat = constructRetinexSparseMat(iw,ih);
	//m_retinexEnergyMat = ublas_cm_f(pixelCnt,pixelCnt);

	m_allConsVec = ublas_vec_f(pixelCnt);
	for (int i = 0; i < pixelCnt; i++)
	{
		m_allConsVec(i) = 0;
	}
	//
	mat_f wMat[] = {mat_f(ih,iw),mat_f(ih,iw),mat_f(ih,iw)};
	mat_f diMat[] = {mat_f(ih,iw),mat_f(ih,iw),mat_f(ih,iw)};

	wMat[0] = 0;
	wMat[1] = 0;
	diMat[0] = 0;
	diMat[1] = 0;

	int dx[] = {0, 1, 1};
	int dy[] = {1, 0, 1};
	mat_3f chromImg = m_dm.getChrom();
	int dirUse = 2;

	ConstShadeScribble& css = m_shadeScrib;
	mat_3f tmp(m_pixNorm.size());
	tmp = cv::Vec3f(1,1,1);
	mat_u clrEdgeMsk = _getClrEdgeMsk(3);

	for (int i = 0; i < ih - 1; i++)
	{
		for (int j = 0; j < iw - 1; j++)
		{
			if (!m_ROIMask(i,j))
			{
				continue; //skip unmasked image
			}
			int pyi = i;
			int pxi = j;
			cv::Vec3f c1 = chromImg(pyi,pxi);
			cv::Vec3f rgb1 = m_img(pyi,pxi);
			cv::Vec3f pnr1 = m_pixNorm(pyi,pxi);
			for (int k = 0; k < dirUse; k++)
			{
				int pyj = i + dy[k];
				int pxj = j + dx[k];
				if (!m_ROIMask(pyj,pxj))
				{
					continue;
				}
				cv::Vec3f rgb2 = m_img(pyj,pxj);
				cv::Vec3f c2 = chromImg(pyj,pxj);
				cv::Vec3f pnr2 = m_pixNorm(pyj,pxj);
				diMat[k](i,j) = m_logImg(pyi,pxi) - m_logImg(pyj,pxj);// Ii - Ij

				float clrDist = cv::norm(rgb1 - rgb2);

				float normDist = -1;
				if (cv::norm(pnr1) > 1e-5 && cv::norm(pnr2) > 1e-5)
				{
					normDist = pnr1.ddot(pnr2);
				}
				float chromDist = Utility::vecDist(c1,c2);
				float clrThrd = 0.1;

				if (chromDist < IMConfig::chromThrd)
				{
					wMat[k](i,j) = IMConfig::rWeight;
				}

				//if (clrDist < clrThrd)
				//{
				//	wMat[k](i,j) = IMConfig::rWeight;
				//}

				//if (!clrEdgeMsk(pyi,pxi) && !clrEdgeMsk(pyj,pxj) && clrDist < clrThrd)//
				//{
				//	wMat[k](i,j) = IMConfig::rWeight;
				//}

				//if (clrDist <= clrThrd || (chromDist <= IMConfig::chromThrd && normDist < 0))//chromDist < IMConfig::chromThrd
				//{
				//	wMat[k](i,j) = IMConfig::rWeight;
				//}

			}
		}
	}
	mat_3f visNorm = (m_pixNorm + tmp);
	visNorm /= 2;
	//construct the energy matrix
	float sWeight = 1;
	for (int i = 0; i < ih; i++)
	{
		for (int j = 0; j < iw; j++)
		{
			int pi = i * iw + j;
			if (!m_ROIMask(i,j))
			{
				continue;
			}
			for (int k = 0; k < dirUse; k++)
			{
				int pjx = j + dx[k];
				int pjy = i + dy[k];
				if (!m_ROIMask(pjy,pjx) || pjx < 0 || pjx >= iw || pjy < 0 || pjy >= ih)
				{
					continue;
				}
				int pj = pjx + pjy * iw;
				float w2 = wMat[k](i,j) + sWeight;
				m_retinexEnergyMat(pi,pi) += w2;
				m_retinexEnergyMat(pj,pj) += w2;
				m_retinexEnergyMat(pi,pj) -= w2;
				m_retinexEnergyMat(pj,pi) -= w2;
				m_allConsVec(pi) += (wMat[k](i,j) * diMat[k](i,j));
				m_allConsVec(pj) -= (wMat[k](i,j) * diMat[k](i,j));
			}
		}
	}

	//
	m_allConsMat = m_retinexEnergyMat; //

}


void RetinexIntrinsic::_solve(){
	//
	//saveSparseMatrix();
	if(m_solutionVec.empty())
		m_solutionVec = m_allConsVec;
	m_solutionVec = MatLab::ref().sparseLinSolve(m_allConsMat,m_allConsVec);
	m_solveTime = MatLab::ref().m_linSolveTime; //get the solution time
	m_matrixTime = MatLab::ref().m_matrixTime; //get the matrix time
	for (int i = 0; i < m_solutionVec.size(); i++)
	{
		m_solutionVec(i) = exp(m_solutionVec(i)); //
	}
}


void RetinexIntrinsic::addColorPlaneConstraint(){
	//adding color planar constraint in the log space
	mat_3f imgBK = m_img.clone();
	m_img = m_logImg.clone(); //
	m_matBuild = false;//
	_buildLaplacianMatrix(); //build the laplacian matrix
	//
	m_allConsMat = m_allConsMat +  m_sLapmat; //update the constraint
	//
	m_img = imgBK.clone(); //

}


void RetinexIntrinsic::_init(){
	_buildRetinexEnergyMat();
}


void RetinexIntrinsic::_albedoConstraint2SparseMat(){
	//
	IntrinsicModel::_albedoConstraint2SparseMat(); //initialize the matrix and vector
	int iw = m_img.size().width;
	int ih = m_img.size().height;
	for (int i = 0; i < m_cr.size(); i++)
	{
		GrpEle stroke = m_cr[i];
		int s_sz = stroke.m_eMember.size();
		float n_factor = 1.0 / s_sz;
		if (!m_eqCons)
		{
			for (int j = 0; j < s_sz; j++)
			{
				int r_px = stroke.m_eMember[j].m_eleID;
				float conf1 = stroke.m_eMember[j].m_conf;
				float Ii = m_logImg(r_px / iw, r_px % iw);
				for (int k = j + 1; k < s_sz; k++)
				{
					int c_px = stroke.m_eMember[k].m_eleID;
					float Ij = m_logImg(c_px / iw, c_px % iw);
					float conf2 = stroke.m_eMember[k].m_conf;
					float fac = (conf1 + conf2) * n_factor;

					m_albedoConsMat(r_px,r_px) += fac;
					m_albedoConsMat(c_px,c_px) += fac;
					m_albedoConsMat(r_px,c_px) -= fac;
					m_albedoConsMat(c_px,r_px) -= fac;

					m_albedoConsVec(r_px) += fac * (Ii - Ij);
					m_albedoConsVec(c_px) += fac * (Ij - Ii);
				}
			}
		}else{
			for (int k = 0; k < s_sz - 1; k++)
			{
				int r_px = stroke.m_eMember[k].m_eleID;
				int c_px = stroke.m_eMember[k+1].m_eleID;
				float Ii = m_logImg(r_px / iw, r_px % iw);
				float Ij = m_logImg(c_px / iw, c_px % iw);
				float conf1 = stroke.m_eMember[k].m_conf;
				float conf2 = stroke.m_eMember[k+1].m_conf;
				float tmp = (conf1 + conf2) * m_crLambda;
				m_albedoConsMat(r_px,r_px) += tmp;
				m_albedoConsMat(r_px,c_px) -= tmp;
				m_albedoConsMat(c_px,r_px) -= tmp;
				m_albedoConsMat(c_px,c_px) += tmp;
				m_albedoConsVec(r_px) += tmp * (Ii - Ij);
				m_albedoConsVec(c_px) += tmp * (Ij - Ii);
			}
		}
	}
}


RetinexIntrinsic::~RetinexIntrinsic(){
}
