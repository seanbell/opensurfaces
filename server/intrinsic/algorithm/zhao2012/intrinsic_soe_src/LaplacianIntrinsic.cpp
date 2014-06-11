#include "LaplacianIntrinsic.h"

LaplacianIntrinsic::LaplacianIntrinsic(mat_3f img,int lWinSize)
:IntrinsicModel(img,"LI")
{
	//
	m_lWinSize = lWinSize; //set the window size

}

void LaplacianIntrinsic::_init(){
	_buildLaplacianMatrix();
	m_allConsMat = m_sLapmat; //
	int iw = m_img.size().width;
	int ih = m_img.size().height;
	m_allConsVec = ublas_vec_f(iw * ih);
	for (int i = 0; i < iw * ih; i++)
	{
		m_allConsVec(i) = 0;
	}
	//

}

ublas_vec_f LaplacianIntrinsic::GSOptimize( ublas_vec_f& u0, int iterCnt, float m_lambdaConstrain,float epsilon){
	DataManager* m_dmPtr = &m_dm;
	mat_3f inputImg = m_dmPtr->getInput();
	mat_3f& resultImg = m_dmPtr->getShading(); //the result is the shading image
	int iw = resultImg.size().width;
	int ih = resultImg.size().height;

	int weight = 0.5;
	for (int i = 0; i < ih; i++)
	{
		for (int j = 0; j < iw; j++)
		{
			float val = u0(i * iw + j);
			resultImg(i,j) = cv::Vec3f(val,val,val);
		}
	}
	int hLWinSize = m_lWinSize/2;
	int sizeN = 2 * 2 * hLWinSize + 1;
	int sizeN2 = sizeN * sizeN; 

	ConstShadeScribble* cssPtr = (m_isCS)? &m_shadeScrib: NULL;
	ConstAlbedoScribble* casPtr = (m_isCR)? &m_albedoScrib: NULL;
	AbsoluteShadeScribble* assPtr = (m_isAbsS)? &m_absShadeScrib: NULL;

	ublas_vec_f uVec(u0);
	ublas_vec_f lastVec(uVec);

	for (int i = 0; i != iterCnt ; i++)
	{
		std::cout << "Iter:" << i+1 << std::endl;
		if (cssPtr)
		{
			cssPtr->updateScrVal();
		}
		if (casPtr)
		{
			casPtr->updateScrVal();
		}

		//Guass-Seidel iteration with the Laplacian matrix
		for (int y = 0; y < ih; y++)
		{
			for (int x = 0; x < iw; x++)
			{

				float rv = 0.0f;
				if (assPtr && assPtr->isScr(y,x))
				{
					rv = assPtr->scrVal(y,x)[0];
					//std::cout << rv << std::endl;
				}
				else{
					int i = y * iw + x; //row number for current pixel
					float denom;
					for (int k = 0; k < sizeN2; k++)
					{
						if (m_lapMat(i,k)!=0)
						{
							//coordinate of the corresponding pixel in the image
							int yjc = y + k/sizeN - 2 * hLWinSize;
							int xjc = x + k%sizeN - 2 * hLWinSize;
							if (x == xjc && y == yjc)//diagonal
							{
								denom = m_lapMat(i,k);
							}else{
								//cv::Vec3f tmpRes = resultImg(yjc,xjc);
								//relaxation
								rv -= (m_lapMat(i,k) * uVec(yjc * iw + xjc)); //r
							}
						}
					}
					rv /= denom;
					//std::cout << resVal[0] << std::endl;
					//-- constraint updates
					//check constant-albedo
					if (casPtr && casPtr->isScr(y,x))//constant-reflectance pixel
					{
						//get the scribble id
						int id = casPtr->scrIdx(y,x);
						//get the image value for this pixel
						cv::Vec3f imgVal = inputImg(y,x); 
						rv = (1- m_lambdaConstrain) * rv + m_lambdaConstrain * imgVal[0] * casPtr->scrVal(y,x)[0];
					}
					else{
						if (cssPtr && cssPtr->isScr(y,x))
						{
							int id = cssPtr->scrIdx(y,x);
							rv = (1.0 - m_lambdaConstrain) * rv + m_lambdaConstrain * cssPtr->scrVal(y,x)[0];
						}
					}
				}
				uVec(y * iw + x)  = rv;
				resultImg(y,x) = cv::Vec3f(rv,rv,rv);
			}

		}
		////observer the solution change
		float change = ublas::norm_1(uVec - lastVec) / u0.size();
		if (change < epsilon)
		{
			std::cout <<"change:" <<  change << std::endl;
			break;
		}
		lastVec = uVec;
		//cv::imshow("sd",resultImg);
		//cv::waitKey(1);
	}

	//set the result to shading image
	for (int i = 0; i < ih; i++)
	{
		for (int j = 0;j < iw; j++)
		{
			float val = uVec(i * iw + j);
			resultImg(i,j) = cv::Vec3f(val,val,val);
		}
	}

	return uVec;
}

void LaplacianIntrinsic::_solve(){
	m_solutionVec = MatLab::ref().sparseLinSolve(m_allConsMat,m_allConsVec);
	m_solveTime = MatLab::ref().m_linSolveTime;
	m_matrixTime = MatLab::ref().m_matrixTime;
}



void LaplacianIntrinsic::_albedoConstraint2SparseMat(){
	//
	IntrinsicModel::_albedoConstraint2SparseMat();
	//
	int iw = m_img.size().width;
	int ih = m_img.size().height;

	for (int i = 0; i < m_cr.size(); i++)
	{
		GrpEle stroke = m_cr[i];
		int s_sz = stroke.m_eMember.size();
		if(!m_eqCons){
			float n_factor = 1.0 / s_sz;
			for (int j = 0; j < s_sz; j++)
			{
				int r_px = stroke.m_eMember[j].m_eleID;
				float Ii = m_grayImg(r_px / iw, r_px % iw);
				float conf1 = stroke.m_eMember[j].m_conf;
				for (int k = j + 1; k < s_sz; k++)
				{
					int c_px = stroke.m_eMember[k].m_eleID;
					float Ij = m_grayImg(c_px / iw, c_px % iw);
					float conf2 = stroke.m_eMember[k].m_conf;
					float tmpW = (conf1 + conf2) * n_factor;
					m_albedoConsMat(r_px,r_px) += tmpW * Ij * Ij;
					m_albedoConsMat(r_px,c_px) -= tmpW * Ii * Ij;
					m_albedoConsMat(c_px,c_px) += tmpW * Ii * Ii;
					m_albedoConsMat(c_px,r_px) -= tmpW * Ii * Ij;
				}
			}
		}else{
			for (int k = 0; k < s_sz -1 ; k++)
			{
				int r_px = stroke.m_eMember[k].m_eleID;
				int c_px = stroke.m_eMember[k+1].m_eleID;
				int Ii = m_grayImg(r_px / iw, r_px % iw);
				int Ij = m_grayImg(c_px / iw, c_px % iw);
				m_albedoConsMat(r_px,r_px) += m_crLambda * (Ij * Ij);
				m_albedoConsMat(r_px,c_px) -= m_crLambda * (Ii * Ij);
				m_albedoConsMat(c_px,r_px) -= m_crLambda * (Ii * Ij);
				m_albedoConsMat(c_px,c_px) += m_crLambda * (Ii * Ii);
			}
		}
	}
}


//void LaplacianIntrinsic::_absoluteShadeConstraint2SparseMat(){
//	//
//	int iw = m_img.size().width;
//	int ih = m_img.size().height;
//	float lambda = 100;
//	this->m_absConsVec = ublas_vec_f(iw * ih);
//	for (int i = 0; i < iw * ih; i++)
//	{
//		m_absConsVec(i) = 0;
//	}
//	Constraint absShadeCons = m_absShadeScrib.m_scrPix;
//	m_absConsMat = constructSparseMat(absShadeCons, iw * ih, iw * ih);
//	for (int i = 0;i < absShadeCons.size(); i++)
//	{
//		GrpEle stroke = absShadeCons[i];
//		for (int j = 0; j < stroke.m_eMember.size(); j++)
//		{
//			int pid = stroke.m_eMember[j].m_eleID;
//			m_absConsMat(pid,pid) = lambda; //1 * lambda
//			m_absConsVec(pid) = lambda * m_absShadeScrib.scrVal(pid / iw, pid % iw)[0]; //get the absolute shading value
//		}
//	}
//
//}
