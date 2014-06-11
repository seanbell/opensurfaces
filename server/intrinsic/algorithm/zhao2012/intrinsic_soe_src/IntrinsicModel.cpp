#include "IntrinsicModel.h"
#include <iostream>
#include <fstream>
#include "Utility.h"
#include "SparseMat.h"
#include <cstdio>
#include <boost/filesystem.hpp>

float IMConfig::absLambda = 1000;
float IMConfig::albedoLambda  = 1;
float IMConfig::shadeLambda = 1;
float IMConfig::windowSize = 3;
float IMConfig::chromThrd = 0.005;
float IMConfig::distThrd = 0.0005;
float IMConfig::txVar = 0.1;
float IMConfig::rWeight = 100;
bool IMConfig::useEqCons = true;

ublas_cm_f constructShadeSparseMat(Constraint& cons,int w, int h )
{
	int nzCnt = 0;
	for (int i = 0; i < cons.size(); i++)
	{
		GrpEle& ge = cons[i];
		int geSize = ge.m_eMember.size();
		nzCnt += geSize * 4;
	}
	std::cout << "image size:" << w << "," << h << std::endl;
	float fSz = (float)w * (float)h * (float)w * (float)h;
	std::cout << "matrix size: :" << fSz << ",nzcnt:" << nzCnt << ",sparsity:" << (float)nzCnt/fSz << std::endl;
	return ublas_cm_f(h * w,h * w,nzCnt);
}

ublas_cm_f constructAlbedoSparseMat(Constraint& cons,int w ,int h){
	//
	return constructShadeSparseMat(cons,w,h);
}
ublas_cm_f constructRetinexSparseMat(int w ,int h){
	//
	int nzCnt = w * h * 8;
	return ublas_cm_f(w * h , w * h, nzCnt);
}



IntrinsicModel::IntrinsicModel(mat_3f img,std::string modelName)
:m_img(img.clone())
,m_modelName(modelName)
,m_shadeScrib(NULL,NULL)
,m_albedoScrib(NULL,NULL)
,m_absShadeScrib(NULL,NULL)
,m_eqCons(IMConfig::useEqCons),m_isCS(false),m_isCR(false),m_isAbsS(false),m_cpnInited(false)
,m_csLambda(IMConfig::shadeLambda),m_crLambda(IMConfig::albedoLambda),m_absLambda(IMConfig::absLambda)
,m_sparsity(0)
,m_matBuild(false)
,m_lWinSize(3)
,m_matrixTime(0){

	for (int i = 0; i < m_img.size().height; i++)
	{
		for (int j = 0; j <m_img.size().width; j++)
		{
			m_img(i,j)[0] += 1e-5;
			m_img(i,j)[1] += 1e-5;
			m_img(i,j)[2] += 1e-5;

		}
	}
	m_csInited = false;
	m_crInited = false;
	m_absInited = false;
	m_dm.init(m_img); //intialize the data manager
	m_ROIMask = mat_u(m_img.size());
	m_ROIMask = 255; //set all front pixels
	m_featureMask = mat_u(m_img.size());
	m_featureMask = 255;
	int iw = m_img.size().width;
	int ih = m_img.size().height;
	m_pixNorm = mat_3f(ih,iw);
	m_pixNorm = cv::Vec3f(0,0,0); //initialize as zero vectors
	m_grayImg = mat_f(m_img.size());
	m_logImg = mat_f(m_img.size());
	for (int i = 0; i < ih; i++)
	{
		for (int j = 0; j < iw; j++)
		{
			m_grayImg(i,j) = cv::norm(m_img(i,j)); //
			m_logImg(i,j) = log(m_grayImg(i,j));
		}
	}
	//init the linear equation matrix
	int matSz = m_img.size().width * m_img.size().height;
	m_allConsMat = ublas_cm_f(matSz,matSz);
	m_allConsVec = ublas_vec_f(matSz);
	for(int i = 0; i <matSz; i++)
		m_allConsVec(i) = 0;

}
void setMask(mat_u dstMsk, mat_3f srcMsk = mat_u(0,0)){
	cv::Size mskSz = srcMsk.size();
	dstMsk = 255;
	if (mskSz.width > 0 && mskSz.height > 0)
	{
		for (int i = 0; i < mskSz.height; i++)
		{
			for (int j = 0; j < mskSz.width; j++)
			{
				if (srcMsk(i,j)[0] == 0 )
				{
					dstMsk(i,j) = 0;
				}
			}
		}
	}

}
void IntrinsicModel::setROIMask(mat_3f maskImg){
	::setMask(m_ROIMask,maskImg);
	m_dm.getMask() = m_ROIMask.clone();
}

void IntrinsicModel::setFeatureMask(mat_3f maskImg){
	::setMask(m_featureMask,maskImg);
}


void IntrinsicModel::addShadeScrib(Constraint& cons,float w){
	Constraint filterCons;
	for (int i = 0; i < cons.size(); i++)
	{
		GrpEle& ge = cons[i];
		if (ge.m_eMember.size() > 1)
		{
			filterCons.push_back(ge);
		}
	}
	m_cs = maskConstraint(filterCons);
	m_shadeScrib.m_dmPtr = &m_dm;
	m_shadeScrib.m_strokePtr = &m_cs;
	m_shadeScrib.initScribbles();
	m_isCS = true;
	m_csInited = false;
}

void IntrinsicModel::addAlbedoScrib(Constraint& cons,float w){
	Constraint filterCons;
	for (int i = 0; i < cons.size(); i++)
	{
		GrpEle& ge = cons[i];
		if (ge.m_eMember.size() > 1)
		{
			filterCons.push_back(ge);
		}
	}

	m_cr = maskConstraint(filterCons);
	m_albedoScrib.m_dmPtr = &m_dm;
	m_albedoScrib.m_strokePtr = &m_cr;
	m_albedoScrib.initScribbles();
	m_crInited = false;
	m_isCR = true;
}

void IntrinsicModel::addAbsShadeScrib(Constraint& cons, float w){
	m_abs = maskConstraint(cons);
	m_absShadeScrib.m_dmPtr = &m_dm;
	m_absShadeScrib.m_strokePtr = &m_abs;
	m_absShadeScrib.initScribbles();
	m_absInited= false;
	m_isAbsS = true;
}

Constraint IntrinsicModel::genConsAlbedoCons(float distThrd , float varThrd ){
	//use texture matching
	m_tpgs.m_dmPtr = &m_dm;
	m_tpgs.m_trd_dist = distThrd;
	m_tpgs.m_trd_chrvar = varThrd;
	m_tpgs.reset(); //clear all
	m_tpgs.group();
	return m_tpgs.m_groups; //get the constraint
}

Constraint IntrinsicModel::genConsShadeCons(){
	Constraint cons;
	return cons;
}

Constraint IntrinsicModel::genAbsShadeCons(float absVal){
	int iw = m_img.size().width;
	int ih = m_img.size().height;

	float maxVal = 0;
	int my = 0,mx = 0;
	for (int i = 0; i < ih; i++)
	{
		for (int j = 0; j < iw; j++)
		{
			float tmpVal = cv::norm(m_img(i,j));
			if (tmpVal > maxVal)
			{
				maxVal = tmpVal;
				my = i;
				mx = j;
			}
		}
	}
	Constraint cons;
	GrpEle grp;
	Element ele(my* iw + mx,1.0);
	ele.m_rgb = cv::Vec3f(absVal,absVal,absVal); // set a triple
	grp.m_eMember.push_back(ele);
	cons.push_back(grp);
	return cons;
}


void IntrinsicModel::reduceSdEdge(){
	//eliminate the possible sharp shading edges caused by color planar assumption
	//only process pixels at the color edge
	//using reflectance result as guidance
	mat_3f chromImg = m_dm.getChrom();
	//cv::imshow("chrom",refImg);
	//cv::waitKey(0);
	mat_3f sdImg = m_dm.getShading();
	mat_3f sdBk = sdImg.clone();
	int ih = sdImg.size().height;
	int iw = sdImg.size().width;
	int dx[] ={0,1,1};
	int dy[] = {1,0,1};
	int avgWinSz = 3;
	int hSz = avgWinSz / 2;

	float *weight = new float[avgWinSz * avgWinSz];
	bool distWeighted = false;
	float sum = 0;
	for (int i = - hSz; i <= hSz; i++)
	{
		for (int j = -hSz; j <= hSz; j++)
		{
			int  y = i + hSz;
			int  x = j + hSz;
			float tmpW;
			if (distWeighted)
			{
				float tmp = float(i * i + j * j) / (hSz * hSz);
				tmpW = std::exp(-tmp);
			}
			else
				tmpW = 1;
			weight[y * avgWinSz + x] = tmpW;
		}
	}

	mat_3f edgeImg(ih,iw);
	edgeImg = cv::Vec3f(0,0,0);
	for (int i = 0; i < ih - 1; i++)
	{
		for (int j = 0; j < iw - 1; j++)
		{
			if (!m_ROIMask(i,j))
			{
				continue;
			}
			cv::Vec3f r1 = chromImg(i,j);
			std::vector<int> nx;
			std::vector<int> ny;

			for (int k = 0; k < 3; k++)
			{
				int i1= i + dy[k];
				int j1 = j + dx[k];
				cv::Vec3f r2 = chromImg(i1,j1);

				if(Utility::vecDist(r1,r2) > 0.025){
					nx.push_back(-dx[k]);
					ny.push_back(-dy[k]);
					nx.push_back(dx[k]);
					ny.push_back(dy[k]);
					edgeImg(i,j) = cv::Vec3f(1,1,1);
				}
			}
			if (nx.empty())
			{
				continue;
			}
			cv::Vec3f avgVec(0,0,0);
			int ncnt = 0;
			for (int k1 = 0; k1 < nx.size(); k1++)
			{
				int y = i + ny[k1];
				int x = j + nx[k1];
				if ( y < 0 || y >= ih || x < 0|| x >= iw || !m_ROIMask(y,x))
				{
					continue;
				}
				avgVec += sdImg(y,x);
				ncnt++;
			}
			avgVec[0] /= ncnt;
			avgVec[1] /= ncnt;
			avgVec[2] /= ncnt;
			sdImg(i,j) = avgVec;
		}
	}
	//sdBk.copyTo(sdImg); //
	//cv::imshow("edge",edgeImg);
	//cv::waitKey(0);
}

void IntrinsicModel::decompose( bool normSd /*= false*/,bool normRef /*= false*/,bool wse /*= false*/, bool gamma /*= false*/ )
{
	int iw = m_img.size().width;
	int ih = m_img.size().height;
	mat_3f sdImg = m_dm.getShading();
	mat_3f refImg = m_dm.getAlbedo();

	if (wse)
	{
		reduceSdEdge(); //
	}
	//do gamma correction
	if (normSd)
	{
		//cv::imshow("mask",m_ROIMask);
		//cv::waitKey(0);

		DataManager::normalizeImage(sdImg,m_ROIMask);
	}
	if (normRef)
	{
		DataManager::normalizeImage(refImg,m_ROIMask);
	}

	if (gamma)
	{
		float gval = 2.2;
		IntrinsicModel::gammaCorrect(sdImg,gval);
		IntrinsicModel::gammaCorrect(refImg,gval);
	}

	//sdImg *= 1.5;
}

Constraint  IntrinsicModel::maskConstraint(Constraint& cons){
	Constraint mCons;
	int h = m_img.size().height;
	int w = m_img.size().width;
	for (int i = 0; i <cons.size(); i++)
	{
		GrpEle& ge = cons[i];
		GrpEle ge1 = ge;
		ge1.m_eMember.clear();
		for (int j = 0; j <ge.m_eMember.size(); j++)
		{
			Element& ele = ge.m_eMember[j];
			int py = ele.m_eleID / w;
			int px = ele.m_eleID % w;
			if (m_ROIMask(py,px))
			{
				ge1.m_eMember.push_back(ele);
			}
		}
		if (ge1.m_eMember.size() > 0)
		{
			mCons.push_back(ge1);
		}
	}
	return mCons;
}
Constraint IntrinsicModel::dszCons(int sz11, int sz12, Constraint cons){
	//
	int sz21 = sz11 >> 1;
	int sz22 = sz12 >> 1;

	mat_i sMat(sz21,sz22);
	sMat = 1;
	Constraint dszCons;
	for (int i = 0;i < cons.size(); i++)
	{
		GrpEle ge = cons[i];
		if (ge.m_eMember.empty())
		{
			continue;
		}
		GrpEle ge1 = ge;
		ge1.m_eMember.clear();
		for (int j = 0; j < ge.m_eMember.size() ;j++)
		{
			Element ele1 = ge.m_eMember[j];
			int px = ge.m_eMember[j].m_eleID % sz12;
			int py = ge.m_eMember[j].m_eleID / sz12;
			px >>= 1;
			py >>= 1;
			if (px >= 0 && px < sz22 && py >= 0 && py < sz21 && sMat(py,px))
			{
				ele1.m_eleID = py * sz22 + px;
				ge1.m_eMember.push_back(ele1);
				sMat(py,px) = 0;
			}
		}
		if (!ge1.m_eMember.empty())
		{
			dszCons.push_back(ge1);
		}
	}
	//
	return dszCons;
}

Constraint IntrinsicModel::uszCons(int sz11, int sz12, int sz21, int sz22, Constraint cons){
	Constraint upCons;
	for (int i = 0;i < cons.size(); i++)
	{
		GrpEle ge = cons[i];
		if (ge.m_eMember.empty())
		{
			continue;
		}
		GrpEle ge1 = ge;
		ge1.m_eMember.clear();
		for (int j = 0; j < ge.m_eMember.size() ;j++)
		{
			int px = ge.m_eMember[j].m_eleID % sz12;
			int py = ge.m_eMember[j].m_eleID / sz12;
			px <<= 1;
			py <<= 1;
			if (px >= 0 && px < sz21 && py >= 0 && py < sz22)
				ge1.m_eMember.push_back(Element(py * sz22 + px,ge.m_eMember[j].m_conf));
		}
		if (!ge1.m_eMember.empty())
		{
			upCons.push_back(ge1);
		}
	}
	return upCons;
}

ublas::matrix<mat_f> IntrinsicModel::uszAVec(int sz21, int sz22){
	//
	mat_3f aVecMat2(m_img.size());
	for (int i = 0; i < m_img.size().height; i++)
	{
		for (int j = 0; j < m_img.size().width; j++)
		{
			aVecMat2(i,j) = cv::Vec3f(m_aVecMat(i,j)(0,0),m_aVecMat(i,j)(1,0)
				,m_aVecMat(i,j)(2,0));
		}
	}
	mat_3f uszAVecMat2(sz21,sz22);
	cv::resize(aVecMat2,uszAVecMat2,uszAVecMat2.size(),0,0,cv::INTER_LINEAR);
	ublas::matrix<mat_f> uszAVecMat(sz21,sz22);
	for (int i = 0; i < sz21; i++)
	{
		for (int j = 0; j < sz22; j++)
		{
			uszAVecMat(i,j) = mat_f(3,1);
			uszAVecMat(i,j)(0,0) = uszAVecMat2(i,j)[0];
			uszAVecMat(i,j)(1,0) = uszAVecMat2(i,j)[1];
			uszAVecMat(i,j)(2,0) = uszAVecMat2(i,j)[2];
		}
	}
	return uszAVecMat;
}

void IntrinsicModel::initCPNlMatrix(int m_lWinSize){
	if (!m_cpnInited)
	{
		int hLWinSize = m_lWinSize / 2; //half window size
		int sizeN = 2 * 2 * hLWinSize + 1;
		int numNoneZeroEntry = sizeN * sizeN;
		int iW = m_img.size().width;
		int iH = m_img.size().height;
		//m_sLapmat = ublas_smat_f(iH * iW, iH * iW);
		this->m_mpinvMat = ublas::matrix<mat_f>(iH, iW); //each pixel has an "pinv(m)" matrix
		this->m_aVecMat = ublas::matrix<mat_f>(iH,iW); //"a" vector for each pixel
		//for each local window, construct the local
		int mNumRow = m_lWinSize * m_lWinSize + 3;
		mat_f mMatrix(mNumRow , 3); //matrix defined by Eq (8)
		mat_f invM(3,mNumRow);
		invM = 0;
		mMatrix = 0; //set to zero
		float m_epsilon = 1e-7;
		float sqrtEpsilon = sqrt(m_epsilon);
		mMatrix(mNumRow - 3,0) = mMatrix(mNumRow - 2, 1) = mMatrix(mNumRow - 1,2) = sqrtEpsilon;//set the last three rows
		for (int y = 0; y < iH; y++)
		{
			for (int x = 0; x < iW; x++)
			{
				m_mpinvMat(y,x) = invM;
			}
		}

		for (int y = hLWinSize; y < iH - hLWinSize; y++)
		{
			for (int x = hLWinSize; x < iW - hLWinSize; x++)
			{
				//set the matrix defined in Eq (8)
				if (!m_ROIMask(y,x))
				{
					continue;
				}
				for (int m = - hLWinSize; m <= hLWinSize; m++)
				{

					int yc = y + m;
					for (int n = - hLWinSize; n <= hLWinSize; n++)
					{
						int xc = x +n;
						int tmpIdx = (m + hLWinSize) * m_lWinSize + n + hLWinSize;
						mMatrix( tmpIdx, 0) = m_img(yc,xc)[0];//r
						mMatrix( tmpIdx, 1) = m_img(yc,xc)[1];//g
						mMatrix( tmpIdx, 2) = m_img(yc,xc)[2];//b
					}
				}
				mat_f mPinv = pinv(mMatrix); // pseudo inverse
				m_mpinvMat(y , x) = mPinv; //
			}
		}
		m_cpnInited = true;
	}
}


void IntrinsicModel::_cons2SparseMat(){
	//now formulate the constraint as matrix
	float w = 1.0;
	if(m_isCS){
		std::cout << "constant shading constraint to sparse matrix..." << std::endl;
		if (!m_csInited)
		{
			_shadeConstraint2SparseMat();
			m_csInited = true;
		}
		m_allConsMat = m_allConsMat + w * m_shadeConsMat;
		m_allConsVec += w * m_shadeConsVec;
	}
	if (m_isCR)
	{
		std::cout << "constant albedo constraint to sparse matrix..." << std::endl;
		if(!m_crInited)
		{
			_albedoConstraint2SparseMat();
			m_crInited = true;
		}
		m_allConsMat = m_allConsMat + w * m_albedoConsMat;
		m_allConsVec += w * m_albedoConsVec; //

	}
	if (m_isAbsS)
	{
		std::cout << "absolute shading constraint to sparse matrix..." << std::endl;
		if (!m_absInited)
		{
			_absoluteShadeConstraint2SparseMat();
			m_absInited =true;
		}
		float absW = 1.0;
		m_allConsMat = m_allConsMat + absW * m_absConsMat;
		m_allConsVec += absW * m_absConsVec;

	}
	typedef ublas_cm_f::iterator1 it1_t;
	typedef ublas_cm_f::iterator2 it2_t;
	int nzCnt = 0;
	float iw = m_img.size().width;
	float ih = m_img.size().height;
	for (it2_t it2 = m_allConsMat.begin2();it2 != m_allConsMat.end2(); it2++)
	{
		int idx1, idx2;
		for (it1_t it1 = it2.begin(); it1 != it2.end(); it1++,nzCnt++);
	}
	m_sparsity = double(nzCnt) / double(iw * ih * iw * ih);

}


void IntrinsicModel::lMat2sLmat(){
	//
	int ih = m_img.size().height;
	int iw = m_img.size().width;
	int h = m_lapMat.size1();
	int w = m_lapMat.size2();
	int hLWinSize = m_lWinSize / 2; //half window size
	int sizeN = 2 * 2 * hLWinSize + 1;

	m_sLapmat = ublas_cm_f( iw * ih, iw * ih);


	for (int i = 0; i < iw * ih ;i++)
	{
		int y = i / iw;
		int x = i % iw;
		for (int k = 0; k < w; k++)
		{
			if (m_lapMat(i,k)==0)
			{
				continue;
			}
			int yjc = y + k/sizeN - 2 * hLWinSize;
			int xjc = x + k%sizeN - 2 * hLWinSize;
			//std::cout << "y,x,y1,x1:" << y <<"," << x << "," << yjc << "," << xjc << std::endl;
			//getchar();
			m_sLapmat(i , yjc * iw + xjc) = m_lapMat(i,k);
		}
	}
}

void IntrinsicModel::_buildLaplacianMatrix(){
	std::cout << "initialize laplacian matrix..." << std::endl;
	int hLWinSize = m_lWinSize / 2; //half window size
	int sizeN = 2 * 2 * hLWinSize + 1;
	int numNoneZeroEntry = sizeN * sizeN;
	int iW = m_img.size().width;
	int iH = m_img.size().height;
	m_lapMat = ublas_mat_f(iH * iW, numNoneZeroEntry);
	for (int i = 0;i < m_lapMat.size1(); i++)
	{
		for (int j = 0; j < m_lapMat.size2(); j++)
		{
			m_lapMat(i,j) = 0;
		}
	}
	//for each local window, construct the local
	int mNumRow = m_lWinSize * m_lWinSize + 3;
	mat_f mMatrix(mNumRow , 3); //matrix defined by Eq (8)
	mMatrix = 0; //set to zero
	float m_epsilon = 1e-7;
	float sqrtEpsilon = sqrt(m_epsilon);
	mMatrix(mNumRow - 3,0) = mMatrix(mNumRow - 2, 1) = mMatrix(mNumRow - 1,2) = sqrtEpsilon;//set the last three rows
	for (int y = hLWinSize; y < iH - hLWinSize; y++)
	{
		for (int x = hLWinSize; x < iW - hLWinSize; x++)
		{
			//set the matrix defined in Eq (8)
			for (int m = - hLWinSize; m <= hLWinSize; m++)
			{

				int yc = y + m;
				for (int n = - hLWinSize; n <= hLWinSize; n++)
				{
					int xc = x +n;
					int tmpIdx = (m + hLWinSize) * m_lWinSize + n + hLWinSize;
					mMatrix( tmpIdx, 0) = m_img(yc,xc)[0];//r
					mMatrix( tmpIdx, 1) = m_img(yc,xc)[1];//g
					mMatrix( tmpIdx, 2) = m_img(yc,xc)[2];//b
				}
			}

			mat_f mPinv = pinv(mMatrix); // pseudo inverse
			mat_f mMatrix_mPinv = mMatrix * mPinv; //mi * pinv(mi)
			cv::Size tmpSize = mMatrix_mPinv.size();
			mat_f nMat = mat_f::eye(tmpSize) - mMatrix_mPinv; //n matrix
			cv::Size nMatSize = nMat.size();
			mat_f nMatTrans(cv::Size(nMatSize.width,nMatSize.height));
			cv::transpose(nMat,nMatTrans);
			mat_f nTrans_nMat = nMatTrans * nMat; //
			for (int mi = -hLWinSize; mi <= hLWinSize; mi++)
			{
				int yic = y + mi;
				for (int ni = -hLWinSize; ni <= hLWinSize; ni++)
				{
					int xic = x + ni;
					int i = yic * iW + xic; //pixel (yic, xic), row index in the Laplacian matrix
					int ik = (mi + hLWinSize) * m_lWinSize + ni + hLWinSize;

					for (int mj = -hLWinSize; mj <= hLWinSize; mj++)
					{
						int yjc = y + mj;
						for (int nj = -hLWinSize; nj <= hLWinSize; nj++)
						{
							int xjc = x + nj;
							int jk = (mj + hLWinSize) * m_lWinSize + nj + hLWinSize;
							int j = (yjc - yic + 2 * hLWinSize) * sizeN + (xjc - xic + 2 * hLWinSize);
							m_lapMat(i,j) += nTrans_nMat(ik,jk);
						}
					}
				}
			}
		}
	}
	m_matBuild = true;
	lMat2sLmat();
}


void IntrinsicModel::init()
{
	_init();
}
void IntrinsicModel::computeAVec()
{
	//compute "a" vector for each pixel

	initCPNlMatrix(m_lWinSize);
	int iW = m_img.size().width;
	int iH = m_img.size().height;
	mat_i pixAStatus(iH,iW);
	pixAStatus = 0;
	int hLWinSize = m_lWinSize / 2; //half window size
	//all marginal pixels should use the
	for (int y = 0;y < iH; y++)
	{
		for (int x = 0; x < iW; x++)
		{
			m_aVecMat(y,x) = mat_f(3,1);
			m_aVecMat(y,x) = 0;

			if (y >= hLWinSize && x >= hLWinSize && y < iH - hLWinSize && x < iW - hLWinSize)
			{
				pixAStatus(y,x) = 1;
			}
		}
	}
	//
	mat_3f shadeImg = m_dm.getShading();
	//
	for ( int y = hLWinSize; y < iH - hLWinSize; y++)
	{
		for (int x = hLWinSize; x < iW - hLWinSize; x++)
		{

			if (!m_ROIMask(y,x))
			{
				continue;
			}
			mat_f pmMat = m_mpinvMat(y,x);
			mat_f sVec(m_lWinSize * m_lWinSize + 3,1);
			sVec = 0; //
			int pIdx = 0;
			for (int i = -hLWinSize; i <= hLWinSize; i++)
			{
				int py = i + y;
				for (int j = -hLWinSize; j <= hLWinSize; j++, pIdx++)
				{
					int px = j + x;
					sVec(pIdx,0) = shadeImg(py,px)[0]; //get the shading value
				}
			}
			//now compute the a vector
			mat_f aVec = m_mpinvMat(y,x) * sVec; //
			m_aVecMat(y,x) = aVec;
			for (int i = -hLWinSize; i <= hLWinSize; i++)
			{
				int py = y + i;
				for (int j = -hLWinSize; j <= hLWinSize; j++)
				{
					int px = x + j;
					if (!pixAStatus(py,px) &&m_ROIMask(py,px))
					{
						m_aVecMat(py,px) = aVec;
						pixAStatus(py,px) = 1;
					}
				}
			}
		}
	}
	//average the a vectors
	//avgCPNormal(false);
}

mat_3f IntrinsicModel::aVec2Mat3f(){
	//
	mat_3f vis(m_img.size());
	for (int i = 0; i < m_img.size().height; i++)
	{
		for (int j = 0; j < m_img.size().width; j++)
		{
			mat_f tmpA = m_aVecMat(i,j);
			vis(i,j)[0] = tmpA(0,0);
			vis(i,j)[1] = tmpA(1,0);
			vis(i,j)[2] = tmpA(2,0);
		}
	}
	return vis;
}

void IntrinsicModel::visAVec(){
	mat_3f vis = aVec2Mat3f();
	static int cnt = 0;
	char buffer[256];
	sprintf(buffer,"%s_%d","window",cnt++);
	cv::imshow(buffer,vis);
	cv::waitKey(0);
}


void IntrinsicModel::avgCPNormal(bool distWeithed ){
	//
	int hLWinSize = m_lWinSize / 2;

	int avgWinSz = 3;
	int hSz = avgWinSz / 2;
	float *weight = new float[avgWinSz * avgWinSz];
	float sum = 0;
	for (int i = - hSz; i <= hSz; i++)
	{
		for (int j = -hSz; j <= hSz; j++)
		{
			int  y = i + hSz;
			int  x = j + hSz;
			float tmpW;
			if (distWeithed)
			{
				float tmp = float(i * i + j * j) / (hSz * hSz);
				tmpW = std::exp(-tmp);
			}
			else
				tmpW = 1;
			weight[y * avgWinSz + x] = tmpW;
			sum += tmpW;
		}
	}
	for (int i = 0; i < avgWinSz * avgWinSz; i++)
	{
		weight[i] /= sum;
	}
	//
	int iH = m_img.size().height;
	int iW = m_img.size().width;

	ublas::matrix<mat_f> aVecMatBK(m_aVecMat);

	for (int i = 0; i < iH; i++)
	{
		for (int j = 0; j < iW; j++)
		{
			if (!m_ROIMask(i,j))
			{
				continue;
			}
			mat_f avgVec(3,1);
			avgVec  = 0;
			float wSum = 0;
			for (int k1 = -hSz; k1 <= hSz; k1++)
			{
				for (int k2 = -hSz; k2 <= hSz; k2++)
				{
					int y = i + k1;
					int x = j + k2;
					if ( y < 0 || y >= iH || x < 0 || x >= iW || !m_ROIMask(y,x))
					{
						continue;
					}
					float tmpW =weight[(k1 + hSz) * avgWinSz + k2 + hSz];
					wSum += tmpW;
					mat_f curVec = m_aVecMat(y,x);
					avgVec = avgVec + tmpW * curVec;
				}
			}
			avgVec /= wSum;
			aVecMatBK(i,j) = avgVec.clone();
		}
	}
	m_aVecMat = aVecMatBK;
	delete[] weight;
}



mat_3f IntrinsicModel::decomposeFromAVec(){
	// s = I * a for each pixel
	int iH = m_img.size().height;
	int iW = m_img.size().width;
	mat_3f sImg = m_dm.getShading();
	mat_3f rImg = m_dm.getAlbedo();
	sImg = cv::Vec3f(0,0,0);
	for (int i = 0; i < iH; i++)
	{
		for (int j = 0; j < iW; j++)
		{
			//std::cout << "i,j:" << i <<"," << j << std::endl;
			if (!m_ROIMask(i,j))
			{
				continue;
			}
			mat_f aVec = m_aVecMat(i,j);
			cv::Vec3f rgbVec = m_img(i,j);
			float sVal = aVec(0,0) * rgbVec[0] + aVec(1,0) * rgbVec[1] + aVec(2,0) * rgbVec[2];
			sImg(i,j) = cv::Vec3f(sVal,sVal,sVal);
			sVal = sVal > 1e-8 ? 1/sVal: 0;
			rImg(i,j) = cv::Vec3f(rgbVec[0] * sVal,rgbVec[1] * sVal,rgbVec[2] * sVal);
		}
	}
	return sImg;
}


void IntrinsicModel::solve(){
	m_solveTime = 0.0;
	_cons2SparseMat(); //
	//std::cout << "solve the linear system..." << std::endl;
	_solve();
	//convert the solution vector to shading image
	int iw = m_img.size().width;
	mat_3f sdImg = m_dm.getShading();
	mat_3f inputImg = m_dm.getInput();
	mat_3f refImg = m_dm.getAlbedo();
	for (int i = 0; i < m_solutionVec.size(); i++)
	{
		int px = i % iw;
		int py = i / iw;
		float sdVal = m_solutionVec(i);
		if (!m_ROIMask(py,px))
		{
			sdVal = 0;
		}
		sdImg(py,px) = cv::Vec3f(sdVal,sdVal,sdVal);
		cv::Vec3f rgb = inputImg(py,px);
		sdVal = sdVal > 1e-8? 1/sdVal: 0;
		refImg(py,px) = cv::Vec3f(rgb[0] * sdVal, rgb[1] * sdVal, rgb[2] * sdVal);
	}
	//
}


void IntrinsicModel::saveAlbedoConsVis(std::string basePath, std::string imgName){
	if (m_isCR && m_tpgs.m_dmPtr)
	{
		char buffer[512];
		m_tpgs.saveGrpVis(basePath+"/"+imgName,"tpgs",20);
	}

}

void IntrinsicModel::saveResult(std::string basePath, std::string imgName){
	//save the result
	char subDirName[256];
	//if (m_tpgs.m_dmPtr)
	//{
		//sprintf(subDirName,"%s_%s_%f_%f_%f",imgName.c_str(),m_modelName.c_str(),IMConfig::chromThrd,IMConfig::txVar,IMConfig::distThrd);
	//}else{
		sprintf(subDirName,"%s_%s",imgName.c_str(),m_modelName.c_str());
	//}
	basePath = basePath + "/" +  subDirName;
	//CreateDirectory(basePath.c_str(),NULL); //create the directory

	boost::filesystem::path rootPath ( basePath.c_str() );
	boost::system::error_code returnedError;
	boost::filesystem::create_directories( rootPath, returnedError );

	std::string sdImgPath = basePath + "/" + imgName + "_sd_" + m_modelName + ".png";
	std::string refImgPath = basePath + "/" + imgName + "_ref_" + m_modelName + ".png";
	std::string chromImgPath = basePath + "/" + imgName + "_chrom_" + m_modelName + ".png";

	cv::imwrite(sdImgPath,m_dm.getShading() * 255.0);
	cv::imwrite(refImgPath,m_dm.getAlbedo() * 255.0);
	cv::imwrite(chromImgPath,m_dm.getChrom() * 255.0);
	//save albedo constraints
	//saveAlbedoConsVis(basePath,imgName);
	//save other information
	std::string fname = basePath + "/" + imgName + ".txt";
	FILE* fid = fopen(fname.c_str(),"w");
	int iw = m_img.size().width;
	int ih = m_img.size().height;
	fprintf(fid,"image size: %d x %d\n",ih , iw);
	fprintf(fid,"solution time:%f\n",m_solveTime);
	fprintf(fid,"matrix time:%f\n",m_matrixTime);
	fprintf(fid,"matrix sparsity:%f\n",m_sparsity);
	fclose(fid);

}

//void IntrinsicModel::visConstraint(){
	//int h = m_img.size().height;
	//int w = m_img.size().width;
	//if(m_isCS){
		//verifyUserConstraint(m_shadeScrib.m_scrPix,h ,w);
	//}
	//if (m_isCR)
	//{
		//verifyUserConstraint(m_albedoScrib.m_scrPix,h,w);
	//}
	//if (m_isAbsS)
	//{
		//verifyUserConstraint(m_absShadeScrib.m_scrPix,h,w);
	//}
//}

//#define __USE_SM__


void IntrinsicModel::_shadeConstraint2SparseMat(){
	int iw = m_img.size().width;
	int ih = m_img.size().height;
	Constraint cons = m_shadeScrib.m_scrPix;
	m_shadeConsMat = constructShadeSparseMat(cons,iw,ih);
	m_shadeConsVec = ublas_vec_f(iw * ih);
	for (int i =0; i < iw * ih; i++)
	{
		m_shadeConsVec(i) = 0;
	}
#ifdef __USE_SM__
	SparseMat sm(iw * ih, iw * ih);
#endif

	for (int i = 0;i < cons.size(); i++)
	{
		GrpEle stroke = cons[i];
		//for each pixel stroke, set it as the reference and compute the error
		int s_sz = stroke.m_eMember.size();
		//std::cout << "shading grp size:" << s_sz << std::endl;
		if(!m_eqCons)
		{
			float n_factor = 1.0 / s_sz;
			for (int j = 0; j < s_sz; j++)
			{
				int r_px = stroke.m_eMember[j].m_eleID; //reference pixel
				float conf1 = stroke.m_eMember[j].m_conf;
				for (int k = j + 1; k < s_sz; k++)
				{
					int c_px = stroke.m_eMember[k].m_eleID; //current pixel
					float conf2 = stroke.m_eMember[k].m_conf;
					float tmpW = n_factor * (conf1 + conf2);
					m_shadeConsMat(r_px,r_px) += tmpW;
					m_shadeConsMat(c_px,c_px) += tmpW;
					m_shadeConsMat(r_px,c_px) -= tmpW;
					m_shadeConsMat(c_px,r_px) -= tmpW;
				}
			}
		}
		else{
			for (int k = 0; k < s_sz - 1; k++)
			{
				int r_px = stroke.m_eMember[k].m_eleID;
				int c_px = stroke.m_eMember[k+1].m_eleID;
				float conf1 = stroke.m_eMember[k].m_conf;
				float conf2 = stroke.m_eMember[k+1].m_conf;
				float tmp = (conf1 + conf2) * m_csLambda;
#ifdef __USE_SM__
				sm.addElement(r_px,r_px,tmp);
				sm.addElement(c_px,c_px,tmp);
				sm.addElement(r_px,c_px,-tmp);
				sm.addElement(c_px,r_px,-tmp);
#else
				m_shadeConsMat(r_px,r_px) += tmp;
				m_shadeConsMat(c_px,c_px) += tmp;
				m_shadeConsMat(r_px,c_px) -= tmp;
				m_shadeConsMat(c_px,r_px) -= tmp;
#endif
			}
		}
	}
#ifdef 	__USE_SM__
	sm.merge();
	sm.dumpToFile("d:/ELEZQI/shade_sparse.txt");
#endif
}


void IntrinsicModel::_albedoConstraint2SparseMat(){
	int iw = m_img.size().width;
	int ih = m_img.size().height;
	int pxCnt = ih * iw;
	m_albedoConsMat = constructAlbedoSparseMat(m_cr,iw ,ih);
	//m_albedoConsMat = ublas_cm_f(pxCnt,pxCnt);
	m_albedoConsVec = ublas_vec_f(pxCnt);
	for (int i = 0; i < pxCnt; i++)
	{
		m_albedoConsVec(i) = 0;
	}
}
void IntrinsicModel::_absoluteShadeConstraint2SparseMat(){
	int iw = m_img.size().width;
	int ih = m_img.size().height;
	this->m_absConsMat = ublas_cm_f(iw * ih, iw * ih);
	this->m_absConsVec = ublas_vec_f(iw * ih);
	for (int i = 0; i < iw * ih; i++)
	{
		m_absConsVec(i) = 0;
	}

	Constraint absShadeCons = m_absShadeScrib.m_scrPix;
	//std::cout << "# of abs stroke:" << absShadeCons.size() << std::endl;
	for (int i = 0;i < absShadeCons.size(); i++)
	{
		GrpEle stroke = absShadeCons[i];
		//std::cout<<"stroke size:" << stroke.m_eMember.size() << std::endl;
		for (int j = 0; j < stroke.m_eMember.size(); j++)
		{
			int pid = stroke.m_eMember[j].m_eleID;
			float pval = m_absShadeScrib.scrVal(pid / iw, pid % iw)[0];

			if (m_modelName == "RI")
			{
				pval = log(pval);
			}
			m_absConsMat(pid,pid) = m_absLambda; //1 * lambda
			m_absConsVec(pid) = m_absLambda * pval; //get the absolute shading value
		}
	}
}


void IntrinsicModel::saveConsGrpVal(std::string basePath,std::string imgName){
	//
	char buffer[256];
	if (m_isCS)
	{
		m_shadeScrib.updateScrVal();
		m_shadeScrib.writeScrPixVal(basePath + "/" + imgName + "_cs.txt",false);
		m_shadeScrib.writeScrPixVal(basePath + "/" + imgName + "_cs.png",true);

	}
	if (m_isCR)
	{
		m_albedoScrib.updateScrVal();
		m_albedoScrib.writeScrPixVal(basePath + "/" + imgName + "_cr.txt",false);
		m_albedoScrib.writeScrPixVal(basePath + "/" + imgName + "_cr.png",true);

	}
}


void IntrinsicModel::saveSparseMatrix(std::string rootPath){
	//
	std::string smPath = rootPath + "\\" +"allCons_mat.txt";
	std::string bPath = rootPath + "\\" + "allcons_vec.txt";
	std::string dimPath = rootPath + "\\" + "img_dim.txt";

	typedef ublas_cm_f::iterator1 it1_t;
	typedef ublas_cm_f::iterator2 it2_t;
	ublas_cm_f& resultMat = m_allConsMat;

	std::ofstream ofs;
	ofs.open(smPath.c_str(),std::ios_base::out);
	for (it1_t it1 = resultMat.begin1();it1 != resultMat.end1(); it1++)
	{
		int idx1, idx2;
		for (it2_t it2 = it1.begin(); it2 != it1.end(); it2++)
		{
			idx1 = it2.index1();
			idx2 = it2.index2();
			float eleVal = resultMat(idx1,idx2);
			ofs << idx1 << " " << idx2 << " " << eleVal << "\n";
		}
	}
	ofs.close();
	ofs.open(bPath.c_str(),std::ios::out);

	for (int i = 0; i < m_allConsVec.size(); i++)
	{
		ofs << m_allConsVec(i) << "\n";
	}
	ofs.close();
	//
	ofs.open(dimPath.c_str(),std::ios::out);
	ofs << m_img.size().height << " " << m_img.size().width << "\n";
	ofs.close();
}


void IntrinsicModel::gammaCorrect(mat_3f img, float gamma){
	//
	cv::pow(img,1.0/gamma,img);
}
IntrinsicModel::~IntrinsicModel(){

}


