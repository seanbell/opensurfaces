#if 0
#include "IntrinsicMG.h"
#include "Timer.h"
#include "Utility.h"

IntrinsicLevel::IntrinsicLevel(mat_3f img, int level, int lWinSize,ConstraintPtr consShadePtr,
							   ConstraintPtr constRefPtr,
							   ConstraintPtr absShadePtr)
							   :m_img(img),
							   m_level(level),m_lWinSize(lWinSize)
							   ,m_shadeScrib(NULL,NULL)
							   ,m_albedoScrib(NULL,NULL)
							   ,m_absShadeScrib(NULL,NULL)
							   ,m_isCS(false),m_isCR(false),m_isAbsS(false),m_matBuild(false){
								   m_dm.init(m_img); //intialize the data manager
								   m_shadeStrokeImg = m_img.clone();
								   m_albedoStrokeImg = m_img.clone();
								   m_absShadeImg = m_img.clone();
								   m_shadeStrokeImg = cv::Vec3f(0,0,0);
								   m_albedoStrokeImg = cv::Vec3f(0,0,0);
								   m_absShadeImg = cv::Vec3f(0,0,0);

								   if (consShadePtr)
								   {
									   m_consShade = *consShadePtr;
									   m_shadeScrib.m_dmPtr = &m_dm;
									   m_shadeScrib.m_strokePtr = &m_consShade;
									   m_shadeScrib.initScribbles();
									   setStrokePix(m_shadeStrokeImg,m_shadeScrib.m_scrPix);
									   m_isCS = true;
								   }
								   if (constRefPtr)
								   {
									   m_consRef = *constRefPtr;
									   m_albedoScrib.m_dmPtr = &m_dm;
									   m_albedoScrib.m_strokePtr = &m_consRef;
									   m_albedoScrib.initScribbles();
									   setStrokePix(m_albedoStrokeImg,m_albedoScrib.m_scrPix);
									   m_isCR = true;
								   }
								   if (absShadePtr)
								   {
									   m_absShade = *absShadePtr;
									   m_absShadeScrib.m_dmPtr = &m_dm;
									   m_absShadeScrib.m_strokePtr = &m_absShade;
									   m_absShadeScrib.initScribbles();
									   setStrokePix(m_absShadeImg,m_absShadeScrib.m_scrPix);
									   m_isAbsS = true;
								   }
								  //
								   //cv::imshow("csw",m_shadeStrokeImg );
								   //cv::waitKey(0);								

								   //cv::imshow("caw",m_albedoStrokeImg);
								   //cv::waitKey(0);
								   //cv::imshow("asw",m_absShadeImg);
								   //cv::waitKey(0);

}

void IntrinsicLevel::setStrokePix(mat_3f& strokeImg, Constraint& cons){
	//
	strokeImg = cv::Vec3f(0,0,0);
	int pCnt = 0;
	for (int i = 0; i < cons.size(); i++)
	{
		GrpEle stroke = cons[i];
		for (int j = 0; j < stroke.m_eMember.size(); j++)
		{
			pCnt ++;
			Element ele = stroke.m_eMember[j];
			int px = ele.m_eleID % m_img.size().width;
			int py = ele.m_eleID / m_img.size().width;
			strokeImg(py,px) = ele.m_rgb; //set the rgb value
		}
	}
	//std::cout << "# of pixel in current stroke: " << pCnt << std::endl;
}
IntrinsicLevelPtr IntrinsicLevel::downSample(){
	//downsample the input image
	std::vector<mat_f> planes = splitClrImg(m_img);
	std::vector<mat_f> dPlanes  = std::vector<mat_f>(3);

	for (int i = 0; i < 3; i++)
	{
		dPlanes[i] = dszImg(planes[i]);
	}
	mat_3f dImg = mergeClrImg(dPlanes);
	//downsample the constraints
	ConstraintPtr csPtr  = NULL;
	ConstraintPtr crPtr  = NULL;
	ConstraintPtr absPtr = NULL;
	Constraint cs,cr,abs;
	int h = m_img.size().height;
	int w = m_img.size().width;
	if (m_isCS)
	{
		cs = dszCons(h,w,m_consShade);
		csPtr = &cs;
		//verifyUserConstraint(cs,m_img.size().height,m_img.size().width);
	}
	if (m_isCR)
	{
		cr = dszCons(h,w,m_consRef);
		//verifyUserConstraint(cr,m_img.size().height,m_img.size().width);
		crPtr = &cr;

	}
	if (m_isAbsS)
	{
		abs = dszCons(h,w,m_absShade);
		//verifyUserConstraint(abs,m_img.size().height,m_img.size().width);

		absPtr = &abs;
	}
	//
	IntrinsicLevelPtr im = new IntrinsicLevel(dImg,m_level + 1,m_lWinSize,csPtr,crPtr,absPtr);
	return im;

}


IntrinsicLevelPtr IntrinsicLevel::upSample(int sz1, int sz2){
	std::vector<mat_f> planes = splitClrImg(m_img);
	std::vector<mat_f> dPlanes(3);
	for (int i = 0; i < 3; i++)
	{
		dPlanes[i] = uszImg(planes[i],sz1,sz2);
	}
	mat_3f dImg = mergeClrImg(dPlanes);
	//downsample the constraints
	ConstraintPtr csPtr  = NULL;
	ConstraintPtr crPtr  = NULL;
	ConstraintPtr absPtr = NULL;
	Constraint cs,cr,abs;
	if (m_isCS)
	{
		cs = uszCons(m_img.size().height,m_img.size().width,sz1,sz2,m_consShade);
		csPtr = &cs;
		//verifyUserConstraint(cs,m_img.size().height,m_img.size().width);
	}
	if (m_isCR)
	{
		cr = uszCons(m_img.size().height,m_img.size().width,sz1,sz2,m_consRef);
		//verifyUserConstraint(cr,m_img.size().height,m_img.size().width);
		crPtr = &cr;
	}
	if (m_isAbsS)
	{
		abs = uszCons(m_img.size().height,m_img.size().width,sz1,sz2,m_absShade);
		//verifyUserConstraint(abs,m_img.size().height,m_img.size().width);
		absPtr = &abs;
	}
	//
	IntrinsicLevelPtr im = new IntrinsicLevel(dImg,m_level - 1,m_lWinSize,csPtr,crPtr,absPtr);
	return im;
}

Constraint IntrinsicLevel::dszCons(int sz11, int sz12, Constraint cons){
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

Constraint IntrinsicLevel::uszCons(int sz11, int sz12, int sz21, int sz22, Constraint cons){
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

ublas::matrix<mat_f> IntrinsicLevel::uszAVec(int sz21, int sz22){
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

	std::vector<mat_f> vecPlanes = splitClrImg(aVecMat2);
	std::vector<mat_f> uszPlanes(3);
	for (int i = 0; i < 3; i++)
	{
		uszPlanes[i] = uszImg(vecPlanes[i],sz21,sz22);
	}
	//
	mat_3f uszAVecMat2 =  mergeClrImg(uszPlanes);
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

void IntrinsicLevel::testGSOptimize(){
	//
	int h = m_dm.getImgSize().height;
	int w = m_dm.getImgSize().width;
	ublas_vec_f uVec0(h * w);
	visConstraint();
	for (int i = 0;i < h*w; i++)
	{
		uVec0(i) = 0.5;
	}
	int winsize[] = {3,5,7};
	char buffer[256];
	for (int i = 0; i < 3; i++)
	{
		m_matBuild = false;
		m_lWinSize = winsize[i];
		int iterCnt = 1000;
		//m_lWinSize = 3;
		GSOptimize(uVec0,iterCnt,0.5,1e-6);
		computeAVec(); //compute "a" vector for each pixel
		visAVec();
		mat_3f sdImg = computeShadingFromAVec();
		cv::imshow("sd1",sdImg);
		cv::imshow("sd2",m_dm.getShading());
		cv::waitKey(0);
		decompose();
		mat_3f si = m_dm.getShading().clone();
		mat_3f ri = m_dm.getAlbedo().clone();
		DataManager::normalizeImage(si);
		DataManager::normalizeImage(ri);
		sprintf_s(buffer,"d:/box_fs_%d_%d_shading.png",winsize[i],iterCnt);
		cv::imwrite(std::string(buffer),si * 255.0);
		sprintf_s(buffer,"d:/box_fs_%d_%d_ref.png",winsize[i],iterCnt);
		cv::imwrite(std::string(buffer),ri * 255.0);
	}
}

ublas_vec_f IntrinsicLevel::GSOptimize( ublas_vec_f& u0, int iterCnt, float m_lambdaConstrain,float epsilon){
	//
	if(!m_matBuild)
		buildLMat();
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


void IntrinsicLevel::decompose(){
	//compute the albedo image
	DataManager* m_dmPtr = &m_dm;
	int iw = m_dmPtr->getImgSize().width;
	int ih = m_dmPtr->getImgSize().height;
	mat_3f inputImg = m_dmPtr->getInput();
	mat_3f shadeImg = m_dmPtr->getShading();
	mat_3f refImg = m_dmPtr->getAlbedo();
	for (int i = 0; i < ih; i++)
	{
		for (int j = 0; j < iw; j++)
		{
			cv::Vec3f imgVal = inputImg(i,j);
			cv::Vec3f shadeVal = shadeImg(i,j);
			float r = shadeVal[0] > 1e-8? 1/shadeVal[0]: 0;
			float g = shadeVal[1] > 1e-8? 1/shadeVal[1]: 0;
			float b = shadeVal[2] > 1e-8? 1/shadeVal[2]: 0;
			refImg(i,j)[0] = imgVal[0] * r;
			refImg(i,j)[1] = imgVal[1] * g;
			refImg(i,j)[2] = imgVal[2] * b;
		}
	}
	//cv::imshow("shade",shadeImg);
	//cv::imshow("ref",refImg);
	//cv::waitKey(0);
}


void IntrinsicLevel::buildLMat(){
	if (m_matBuild)
	{
		return;
	}
	std::cout << "initialize laplacian matrix..." << std::endl;
	int hLWinSize = m_lWinSize / 2; //half window size
	int sizeN = 2 * 2 * hLWinSize + 1;
	int numNoneZeroEntry = sizeN * sizeN;
	int iW = m_img.size().width;
	int iH = m_img.size().height;
	m_lapMat = ublas_mat_f(iH * iW, numNoneZeroEntry);
	//m_sLapmat = ublas_smat_f(iH * iW, iH * iW);
	this->m_mpinvMat = ublas::matrix<mat_f>(iH, iW); //each pixel has an "pinv(m)" matrix
	this->m_aVecMat = ublas::matrix<mat_f>(iH,iW); //"a" vector for each pixel
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
			//std::cout << mMatrix << std::endl;
			//getchar();
			//construct the N matrix
			mat_f mPinv = pinv(mMatrix); // pseudo inverse
			m_mpinvMat(y , x) = mPinv; //
			//std::cout << mPinv << std::endl;
			//getchar();
			mat_f mMatrix_mPinv = mMatrix * mPinv; //mi * pinv(mi)
			cv::Size tmpSize = mMatrix_mPinv.size();
			//#ifdef __DEBUG_OUTPUT__
			//			mat_f eyeMat = mat_f::eye(tmpSize);
			//#endif
			mat_f nMat = mat_f::eye(tmpSize) - mMatrix_mPinv; //n matrix
			cv::Size nMatSize = nMat.size();
			mat_f nMatTrans(cv::Size(nMatSize.width,nMatSize.height));
			cv::transpose(nMat,nMatTrans);
			mat_f nTrans_nMat = nMatTrans * nMat; //
			//std::cout << nTrans_nMat << std::endl;
			//getchar();
			//accumulate the values in the L matrix, for each couple of pixels (i,j) covered by the window
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
}

void IntrinsicLevel::computeAVec(){
	//compute "a" vector for each pixel
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

			if (y >= hLWinSize && x >= hLWinSize && y < iH - hLWinSize && x < iW - hLWinSize)
			{
				pixAStatus(y,x) = 1;
			}
		}
	}
	//
	mat_3f shadeImg = m_dm.getShading();
	for ( int y = hLWinSize; y < iH - hLWinSize; y++)
	{
		for (int x = hLWinSize; x < iW - hLWinSize; x++)
		{
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
					if (!pixAStatus(py,px))
					{
						m_aVecMat(py,px) = aVec;
						pixAStatus(py,px) = 1;
					}
				}
			}
		}
	}
}

void IntrinsicLevel::visAVec(){
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
	cv::imshow("vis_a",vis);
	cv::waitKey(0);
}

void IntrinsicLevel::constraint2SparseMat(bool css, bool cas, bool sm){
	//
	std::cout << "build sparse matrix for Laplacian modeling" << std::endl;
	lMat2sLmat();
	m_allConsMat = m_sLapmat;
	if (css)
	{
		std::cout << "build sparse matrix for constant shading constraint" << std::endl;
		shadeConstraint2SparseMat();
		m_allConsMat = m_allConsMat + m_shadeConsMat;
	}
	if (cas)
	{
		std::cout << "build sparse matrix for constant albedo constraint" << std::endl;
		albedoConstraint2SparseMat();
		m_allConsMat = m_allConsMat + m_albedoConsMat;
	}
	if (sm)
	{
		std::cout << "build sparse matrix for shading smoothness constraint" << std::endl;
		shadeSmoothConstraint2SparseMat();
		m_allConsMat = m_allConsMat + m_shadeSmthMat;
	}
	std::cout << "build sparse matrix for absolute shading constraint" << std::endl;
	absoluteShadeConstraint2SparseMat();
	m_allConsMat = m_allConsMat + m_absDiagMat;
}


void IntrinsicLevel::shadeConstraint2SparseMat(){
	//represent the constant shading constraint as sparse matrix
	//for each stroke, select each pixel as the reference and compute the error of remaining pixels against it
	//remember to normalize the sum of error
	int iw = m_img.size().width;
	int ih = m_img.size().height;
	Constraint cons = m_shadeScrib.m_scrPix;
	m_shadeConsMat = constructShadeSparseMat(cons, iw, ih);
	for (int i = 0;i < cons.size(); i++)
	{
		GrpEle stroke = cons[i];
		//for each pixel stroke, set it as the reference and compute the error
		int s_sz = stroke.m_eMember.size();
		float n_factor = 1.0 / s_sz;
		for (int j = 0; j < s_sz; j++)
		{
			int r_px = stroke.m_eMember[j].m_eleID; //reference pixel
			float conf1 = stroke.m_eMember[j].m_conf;
			for (int k = j + 1; k < s_sz; k++)
			{
				int c_px = stroke.m_eMember[k].m_eleID; //current pixel
				float conf2 = stroke.m_eMember[k].m_conf;
				float tmpW = (conf1 + conf2) * n_factor;
				m_shadeConsMat(r_px,r_px) += tmpW;
				m_shadeConsMat(r_px,c_px) -= tmpW;
				m_shadeConsMat(c_px,c_px) += tmpW;
				m_shadeConsMat(c_px,r_px) -= tmpW;
			}
		}
	}
}

void IntrinsicLevel::albedoConstraint2SparseMat(){
	//
	int iw = m_img.size().width;
	int ih = m_img.size().height;
	Constraint cons = m_albedoScrib.m_scrPix;
	m_albedoConsMat = constructAlbedoSparseMat(cons,iw, ih );
	mat_f grayImg(ih,iw);
	for (int i = 0; i < ih; i++)
	{
		for (int j = 0; j < iw; j++)
		{
			grayImg(i,j) = cv::norm(m_img(i,j));
		}
	}

	for (int i = 0; i < cons.size(); i++)
	{
		GrpEle stroke = cons[i];
		int s_sz = stroke.m_eMember.size();
		float n_factor = 1.0 / s_sz;
		for (int j = 0; j < s_sz; j++)
		{
			int r_px = stroke.m_eMember[j].m_eleID;
			float Ii = grayImg(r_px / iw, r_px % iw);
			float conf1 = stroke.m_eMember[j].m_conf;
			for (int k = j + 1; k < s_sz; k++)
			{
				int c_px = stroke.m_eMember[k].m_eleID;
				float Ij = grayImg(c_px / iw, c_px % iw);
				float conf2 = stroke.m_eMember[k].m_conf;
				float tmpW = (conf1 + conf2) * n_factor;
				m_albedoConsMat(r_px,r_px) += tmpW * Ij * Ij;
				m_albedoConsMat(r_px,c_px) -= tmpW * Ii * Ij;
				m_albedoConsMat(c_px,c_px) += tmpW * Ii * Ii;
				m_albedoConsMat(c_px,r_px) -= tmpW * Ii * Ij;
			}
		}
	}
}

void IntrinsicLevel::shadeSmoothConstraint2SparseMat(){
	int iw = m_img.size().width;
	int ih = m_img.size().height;
	m_shadeSmthMat = ublas_cm_f(iw * ih , iw * ih);
	int adj[][2] = {{0,1},{1,0}};
	float lambda = 0.1;
	float twoLambda = lambda * 2;

	//show the chromacity derivative map
	mat_3f hImg(ih , iw);
	hImg = cv::Vec3f(0,0,0);
	mat_3f vImg = hImg.clone();
	std::vector<mat_f> ivec;
	ivec.push_back(hImg);
	ivec.push_back(vImg);
	for (int y = 0;y < ih - 1; y++)
	{
		for (int x = 0; x < iw - 1; x++)
		{
			int p1 = y * iw + x;
			cv::Vec3f chrom1 = m_dm.getChrom()(y,x);
			for (int k = 0; k < 2; k++)
			{
				int y1 = y + adj[k][0];
				int x1 = x + adj[k][1];
				int p2 = y1 * iw + x1;
				cv::Vec3f chrom2 = m_dm.getChrom()(y1,x1);
				if(Utility::vecDist(chrom1,chrom2) > 0.01){//enforcing smoothness constraint
					m_shadeSmthMat(p1,p1) =  lambda;
					m_shadeSmthMat(p1,p2) = -twoLambda;
					m_shadeSmthMat(p2,p2) = lambda;
					mat_3f dImg = ivec[k];
					dImg(y,x) = cv::Vec3f(1,1,1);
				}
			}
		}
	}
	cv::imshow("hdimg",hImg);
	cv::imshow("vdimg",vImg);
	cv::waitKey(0);

}


void IntrinsicLevel::absoluteShadeConstraint2SparseMat(){
	//
	int iw = m_img.size().width;
	int ih = m_img.size().height;
	float lambda = 100;
	this->m_absConsVec = ublas_vec_f(iw * ih);
	for (int i = 0; i < iw * ih; i++)
	{
		m_absConsVec(i) = 0;
	}
	Constraint absShadeCons = m_absShadeScrib.m_scrPix;
	m_absDiagMat = ublas_cm_f(iw * ih, iw * ih);
	for (int i = 0;i < absShadeCons.size(); i++)
	{
		GrpEle stroke = absShadeCons[i];
		for (int j = 0; j < stroke.m_eMember.size(); j++)
		{
			int pid = stroke.m_eMember[j].m_eleID;
			m_absDiagMat(pid,pid) = lambda; //1 * lambda
			m_absConsVec(pid) = lambda * m_absShadeScrib.scrVal(pid / iw, pid % iw)[0]; //get the absolute shading value
		}
	}
}

void IntrinsicLevel::lMat2sLmat(){
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

void IntrinsicLevel::saveImages(std::string basePath,std::string imgName){
	//cv::imshow("csw",m_shadeStrokeImg );
	//cv::waitKey(0);								
	//cv::imshow("caw",m_albedoStrokeImg);
	//cv::waitKey(0);
	//cv::imshow("asw",m_absShadeImg);
	//cv::waitKey(0);
	char buffer[256];
	sprintf_s(buffer,"%s/%s_level%d.png",basePath.c_str(),imgName.c_str(),m_level);
	cv::imwrite(std::string(buffer),m_img * 255);
	sprintf_s(buffer,"%s/%s_level%d_shadeStroke.png",basePath.c_str(),imgName.c_str(),m_level);
	cv::imwrite(std::string(buffer),m_shadeStrokeImg * 255) ;
	sprintf_s(buffer,"%s/%s_level%d_albedoStroke.png",basePath.c_str(),imgName.c_str(),m_level);
	cv::imwrite(std::string(buffer),m_albedoStrokeImg * 255);
	sprintf_s(buffer,"%s/%s_level%d_absShadeStroke.png",basePath.c_str(),imgName.c_str(),m_level);
	cv::imwrite(std::string(buffer),m_absShadeImg * 255);
}

ublas_vec_f IntrinsicLevel::matlabSolve(){
	if(!m_matBuild)
		buildLMat();
	this->constraint2SparseMat(m_isCS,m_isCR);
	Timer tick1;
	tick1.start();
	MatLab& ml = MatLab::ref();
	ublas_vec_f xVec = ml.sparseLinSolve(m_allConsMat,m_absConsVec);
	//now set the result
	mat_3f img = m_dm.getInput();
	mat_3f sImg = m_dm.getShading();
	mat_3f rImg = m_dm.getAlbedo();
	int iw = img.size().width;
	for (int i = 0; i < xVec.size();i++)
	{
		int px = i % iw;
		int py = i / iw;
		float val = xVec(i);
		cv::Vec3f rgb = img(py,px);
		sImg(py,px) = cv::Vec3f(val,val,val);
		rImg(py,px) = cv::Vec3f(rgb[0]/val,rgb[1]/val,rgb[2]/val);
	}
	return xVec;
}

void IntrinsicLevel::saveSparseMat(std::string basePath){
	std::cout << "writing sparse matrix to text file" << std::endl;
	std::string path = basePath + "/" + "allCons_mat.txt";
	FILE* fid = fopen(path.c_str(),"w");
	ublas_cm_f& resultMat = m_allConsMat;
	int iw = m_img.size().width;
	int ih = m_img.size().height;
	typedef ublas_cm_f::iterator1 it1_t; 
	typedef ublas_cm_f::iterator2 it2_t; 
	for (it1_t it1 = resultMat.begin1();it1 != resultMat.end1(); it1++)
	{
		int idx1, idx2;
		for (it2_t it2 = it1.begin(); it2 != it1.end(); it2++)
		{
			idx1 = it2.index1();
			idx2 = it2.index2();
			//std::cout << "idx1,idx2:" << idx1 << ", "<< idx2 << std::endl;
			int y1 = idx1 / iw;
			int x1 = idx1 % iw;
			int y2 = idx2 / iw;
			int x2 = idx2 % iw;
			int idx11 = x1 * ih + y1;
			int idx22 = x2 * ih + y2;
			float eleVal = resultMat(idx1,idx2);
			fprintf(fid,"%d %d %f\n",idx11,idx22,eleVal);
		}
	}
	fclose(fid);
	std::string path1 = basePath + "/" + "right_vec.txt";
	fid = fopen(path1.c_str(),"w");
	for (int i = 0; i < iw; i++)
	{
		for (int j = 0; j < ih; j++)
		{
			fprintf(fid,"%f\n",m_absConsVec(i + j * iw));
		}
	}
	fclose(fid);
	std::string dimPath = basePath + "/" + "img_dim.txt";
	fid = fopen(dimPath.c_str(),"w");
	fprintf(fid,"%d %d",ih,iw);
	fclose(fid);
}

mat_3f IntrinsicLevel::computeShadingFromAVec(){
	// s = I * a for each pixel
	int iH = m_img.size().height;
	int iW = m_img.size().width;
	mat_3f sImg(iH,iW);
	for (int i = 0; i < iH; i++)
	{
		for (int j = 0; j < iW; j++)
		{
			//std::cout << "i,j:" << i <<"," << j << std::endl;
			mat_f aVec = m_aVecMat(i,j);
			cv::Vec3f rgbVec = m_img(i,j);
			sImg(i,j)[0] = aVec(0,0) * rgbVec[0] + aVec(1,0) * rgbVec[1] + aVec(2,0) * rgbVec[2];
			sImg(i,j)[2] = sImg(i,j)[1] = sImg(i,j)[0];
		}
	}
	return sImg;
}


//
void IntrinsicLevel::smoothShading(){
	//if(m_isCS && m_isCR){
	//	//
	//	int iw = m_img.size().width;
	//	int ih = m_img.size().height;

	//	mat_3f sImg = m_dm.getShading();
	//	Constraint& albedoGrps = m_albedoScrib.m_scrPix;
	//	for (int i = 0; i < albedoGrps.size(); i++)
	//	{
	//		GrpEle& grp = albedoGrps[i];
	//		for (int j = 0;j < grp.m_eMember.size(); j++)
	//		{
	//			Element& ele = grp.m_eMember[j];
	//			int px = ele.m_eleID % iw;
	//			int py = ele.m_eleID / iw;
	//			if (!m_shadeScrib.isScr(py,px))
	//			{
	//				continue;
	//			}
	//			cv::Vec3f sVal = m_shadeScrib.scrVal(py,px);
	//			sImg(py,px) = sVal;
	//		}
	//	}
	//}

	if (m_isCR && m_isCS)
	{
		m_shadeScrib.updateScrVal();
		m_albedoScrib.updateScrVal();
		float weight = 0.9;
		int iw = m_img.size().width;
		int ih = m_img.size().height;
		mat_3f sImg = m_dm.getShading();
		Constraint& shadeGrps = m_shadeScrib.m_scrPix;
		for (int i = 0; i < shadeGrps.size(); i++)
		{
			GrpEle& grp = shadeGrps[i];
			for (int j = 0; j < grp.m_eMember.size(); j++)
			{
				Element& ele = grp.m_eMember[j];
				int py = ele.m_eleID / iw;
				int px = ele.m_eleID % iw;
				sImg(py,px) = weight * m_shadeScrib.scrVal(py,px) + (1 - weight) * sImg(py,px);
			}
		}
	}
}

//void IntrinsicLevel::visConstraint(){
	//int h = m_img.size().height;
	//int w = m_img.size().width;
	//if(m_isCS){
		//verifyUserConstraint(m_consShade,h ,w);
	//}
	//if (m_isCR)
	//{
		//verifyUserConstraint(m_consRef,h,w);
	//}
	//if (m_isAbsS)
	//{
		//verifyUserConstraint(m_absShade,h,w);
	//}
//}

std::vector<mat_f> IntrinsicLevel::splitClrImg(mat_3f input){
	int h = input.size().height;
	int w =input.size().width;
	mat_f r(h,w);
	mat_f g = r.clone();
	mat_f b = r.clone();
	for (int i = 0;i < h; i++)
	{
		for (int j = 0; j < w; j++)
		{
			r(i,j) = input(i,j)[0];
			g(i,j) = input(i,j)[1];
			b(i,j) = input(i,j)[2];
		}
	}
	std::vector<mat_f> pVec;
	pVec.push_back(r);
	pVec.push_back(g);
	pVec.push_back(b);
	return pVec;
}

mat_3f IntrinsicLevel::mergeClrImg(std::vector<mat_f>& input){
	//
	int h = input[0].size().height;
	int w = input[0].size().width;
	mat_3f rgb(h,w);
	mat_f r = input[0];
	mat_f g = input[1];
	mat_f b = input[2];
	for (int i = 0;i < h; i++)
	{
		for (int j = 0; j < w; j++)
		{
			rgb(i,j) = cv::Vec3f(r(i,j),g(i,j),b(i,j));
		}
	}
	return rgb;
}

#define  __USE_CV_DSMP__

mat_f IntrinsicLevel::dszImg(mat_f origImg){
	//
	int sz11 = origImg.size().height;
	int sz12 = origImg.size().width;
	int sz21 = sz11 >> 1;
	int sz22 = sz12 >> 1;
	mat_f uImg(sz21,sz22);
	uImg = 0;
#ifndef __USE_CV_DSMP__
	int di[] = { -1, 0 , 1};
	int dj[] = { -1 , 0 , 1};
	float w[] = {
		0.0625, 0.125, 0.0625, 
		0.125, 0.25, 0.125,
		0.0625, 0.125, 0.0625
	};

	uImg = 0;
	for (int i = 0; i < sz21; i++)
	{
		for (int j = 0; j < sz22; j++)
		{
			//std::cout << "i,j" << i << " " << j << std::endl;
			for (int i1 = 0; i1 < 3; i1++)
			{
				int ni = 2 * i + di[i1];
				for (int j1 = 0; j1 < 3; j1++)
				{
					if ( ni >= 0 && ni < sz11 )
					{
						int nj = 2 * j + dj[j1];
						if (nj >= 0 && nj < sz12)
						{
							uImg(i,j) += w[i1 * 3 + j1] * origImg(ni,nj);
						}
					}
				}
			}
		}
	}
#else
	//INTER_LANCZOS4 interpolation method
	cv::resize(origImg,uImg,uImg.size(),0,0,cv::INTER_LANCZOS4);
#endif

	return uImg;

}
mat_f IntrinsicLevel::uszImg(mat_f origImg, int sz21, int sz22){
	int sz11 = origImg.size().height;
	int sz12 = origImg.size().width;


	mat_f dImg(sz21,sz22);
	dImg = 0;
#ifndef __USE_CV_DSMP__
	int di[] = { -1 , 0 , 1};
	int dj[] = { -1 , 0 , 1};
	float w[] = {0.25, 0.5, 0.25, 
		0.5, 1, 0.5,
		0.25, 0.5, 0.25};

	for (int i = 0; i < sz11; i++)
	{
		for (int j = 0; j < sz12; j++)
		{
			for (int i1 = 0; i1 < 3; i1++)
			{
				int ni = 2 * i + di[i1];
				for (int j1 = 0; j1 < 3; j1++)
				{
					if ( ni >= 0 && ni < sz21 )
					{
						int nj = 2 * j + dj[j1];
						if (nj >= 0 && nj < sz22)
						{
							dImg(ni,nj) += w[i1 * 3 + j1] * origImg(i,j);
						}
					}
				}
			}

		}
	}
#else
	cv::resize(origImg,dImg,dImg.size(),0,0,cv::INTER_LANCZOS4);
#endif

	return dImg;
}

ublas_vec_f IntrinsicLevel::cvMat2UblasVec(mat_f mat){
	int h = mat.size().height;
	int w =mat.size().width;
	ublas_vec_f vec(h * w);
	for (int i = 0;i < h; i++)
	{
		for (int j = 0; j < w; j++)
		{
			vec(i * w + j) = mat(i,j);
		}
	}
	return vec;
}


PyramidIntrinsic::PyramidIntrinsic(mat_3f origImg, int lWinSize, int levelCnt, ConstraintPtr conShadePtr,
								   ConstraintPtr consRefPtr, ConstraintPtr absShadePtr,std::string modelName,bool genCons)
								   :IntrinsicModel(origImg,"PI")
								   ,m_levelModelName(modelName)
								   ,m_levelCnt(levelCnt),m_genCons(genCons)
								  
{
	m_lWinSize = lWinSize; //init the local window size
	if (conShadePtr)
	{
		m_isCS = true;
		m_cs = *conShadePtr;
	}
	if (consRefPtr)
	{
		m_isCR = true;
		m_cr = *consRefPtr;
	}
	if (absShadePtr)
	{
		m_isAbsS = true;
		m_abs = *absShadePtr;
	}
}


void PyramidIntrinsic::solveByUszAVec(bool useMatlab ){
	IMPtr botLevel = m_levels[m_levelCnt - 1];
	int h = botLevel->m_img.size().height;
	int w = botLevel->m_img.size().width;
	botLevel->setLocalWindowSize(m_lWinSize);
	botLevel->init();
	
	if (m_genCons && !botLevel->m_isCS)
	{
		botLevel->addShadeScrib(botLevel->genConsShadeCons());
	}

	if (m_genCons && !botLevel->m_isCR)
	{
		botLevel->addAlbedoScrib(botLevel->genConsAlbedoCons(IMConfig::distThrd,IMConfig::txVar));
	}
	if (!botLevel->m_isAbsS)
	{
		botLevel->addAbsShadeScrib(botLevel->genAbsShadeCons(1.0));
	}
	
	botLevel->solve();
	m_botSdImg = botLevel->m_dm.getShading().clone();
	m_botRefImg = botLevel->m_dm.getAlbedo().clone();
	DataManager::normalizeImage(m_botSdImg,botLevel->m_ROIMask);
	DataManager::normalizeImage(m_botRefImg,botLevel->m_ROIMask);

	//cv::imshow("botsd",m_botSdImg);
	//cv::imshow("botref",m_botRefImg);
	//cv::waitKey(0);
	m_solveTime += botLevel->m_solveTime; //
	Timer t;
	t.start();
	botLevel->computeAVec();
	for (int i = m_levelCnt - 1; i >= 0; i --)
	{
		IMPtr curLevel = m_levels[i];
		curLevel->decomposeFromAVec();
		if (i > 0)
		{
			IMPtr nextLevel = m_levels[i - 1];
			int sz21 = nextLevel->m_img.size().height;
			int sz22 = nextLevel->m_img.size().width;
			nextLevel->m_aVecMat = curLevel->uszAVec(sz21,sz22);
		}
	}
	t.stop();
	m_solveTime += t.getElapse();
	std::cout << "time used:" << m_solveTime << "seconds" << std::endl;
	//now copy the result to DataManager of IntrinsicPyramid
	IMPtr topLevel = m_levels[0];
	//copy the shading to pyramid
	m_dm.getShading() = topLevel->m_dm.getShading().clone();
	m_dm.getAlbedo() = topLevel->m_dm.getAlbedo().clone();
	//cv::imshow("sd",m_dm.getShading());
	//cv::imshow("ref",m_dm.getAlbedo());
	//cv::waitKey(0);

}

void PyramidIntrinsic::saveResult(std::string pathBase, std::string imgName){
	//save the result at each level of the pyramid
	char buffer[256];
	//now create a directory to contain results of each level
	int mode = 0;
	if (m_genCons)
	{
		mode = 1;
	}

	sprintf_s(buffer,"%s_%s_%s_%d_%d_%f_%f_%f_%d",imgName.c_str(),m_modelName.c_str(),m_levelModelName.c_str(),m_levelCnt,
		m_lWinSize,IMConfig::chromThrd,IMConfig::txVar,IMConfig::distThrd,mode);
	pathBase = pathBase + "/" +  buffer;
	CreateDirectory(pathBase.c_str(),NULL);
	for (int i = m_levelCnt - 1; i >= 0; i--)
	{
		IMPtr level = m_levels[i];
		level->decompose(true,true); //
		sprintf_s(buffer,"L%d",i);
		CreateDirectory((pathBase + "/" + buffer).c_str(),NULL);
		level->saveResult(pathBase + "/" + buffer,imgName);
	}
	//now save informatino at root level
	IntrinsicModel::saveResult(pathBase,imgName);
	//save the bottom level decomposition which is not from a vector
	sprintf_s(buffer,"%s/%s_botsd.png",pathBase.c_str(),imgName.c_str());
	cv::imwrite(buffer,m_botSdImg * 255.0);
	sprintf_s(buffer,"%s/%s_botref.png",pathBase.c_str(),imgName.c_str());
	cv::imwrite(buffer,m_botRefImg * 255.0);
}

void PyramidIntrinsic::verifyPry(){
	for (int i = 0; i < m_levels.size(); i++ )
	{
		IMPtr tmpLevel = m_levels[i];
		cv::imshow("input",tmpLevel->m_img);
		cv::waitKey(0);
		tmpLevel->visConstraint(); //display the constraint
	}
}

void PyramidIntrinsic::_init(){
	//now build the pyramid
	IMPtr topLevel = NULL;

	releasePyramid();
	if (m_levelModelName == "RI")
	{
		topLevel = new RetinexIntrinsic(m_img,IMConfig::chromThrd);
	}
	else
		topLevel = new LaplacianIntrinsic(m_img,m_lWinSize);
	topLevel->m_ROIMask = m_ROIMask.clone();
	topLevel->m_featureMask = m_featureMask.clone();
	topLevel->setPixNorm(m_pixNorm);
	if (m_isCS)
	{
		topLevel->addShadeScrib(m_cs);
	}
	if (m_isCR)
	{
		topLevel->addAlbedoScrib(m_cr);
	}
	if (m_isAbsS)
	{
		topLevel->addAbsShadeScrib(m_abs);
	}
	topLevel->m_eqCons = IMConfig::useEqCons;
	m_levels.push_back(topLevel);
	//construct subsequent levels
	for (int i = 1; i < m_levelCnt; i++)
	{
		IMPtr aboveLevel = m_levels[i-1];
		IMPtr curLevel = downsampleIM(aboveLevel);
		curLevel->m_eqCons = aboveLevel->m_eqCons;
		curLevel->m_csLambda = aboveLevel->m_csLambda;
		curLevel->m_crLambda = aboveLevel->m_crLambda;
		curLevel->m_absLambda = aboveLevel->m_absLambda;
		m_levels.push_back(curLevel); //
	}

}
void PyramidIntrinsic::_solve(){
	solveByUszAVec(true);
}

void PyramidIntrinsic::releasePyramid(){
	//
	for (int i = 0; i < m_levels.size(); i++)
	{
		delete m_levels[i];
	}
	m_levels.clear();
}

PyramidIntrinsic::~PyramidIntrinsic(){
	releasePyramid();
}


//////////////////////////////////////////////////////////////////////////
float IMConfig::shadeLambda = 100;
float IMConfig::albedoLambda  = 100;
float IMConfig::absLambda  = 1e5;
float IMConfig::windowSize = 3;
bool  IMConfig::useEqCons = true; //
float IMConfig::chromThrd = 0.0001;
float IMConfig::txVar = 0.1;
float IMConfig::distThrd = 0.0005; //distance threshold
float IMConfig::rWeight = 100; //	
//////////////////////////////////////////////////////////////////////////


IntrinsicModel* downsampleIM(IntrinsicModel* imPtr){
	mat_3f m_img = imPtr->m_img;
	int iw = m_img.size().width;
	int ih = m_img.size().height;
	mat_3f dImg(ih/2,iw/2);
	cv::resize(m_img,dImg,dImg.size(),0,0,cv::INTER_NEAREST);
	IntrinsicModel* dsmIM = NULL;
	if (imPtr->m_modelName == "RI")
	{
		RetinexIntrinsic* riPtr = (RetinexIntrinsic*)imPtr;
		dsmIM = new RetinexIntrinsic(dImg,riPtr->m_chromThrd);
	}
	if (imPtr->m_modelName == "LI")
	{
		LaplacianIntrinsic* liPtr = (LaplacianIntrinsic*)imPtr;
		dsmIM = new LaplacianIntrinsic(dImg,liPtr->m_lWinSize);
	}
	dsmIM->m_eqCons = imPtr->m_eqCons;
	if (imPtr->m_isCS)
	{
		Constraint cons = IntrinsicModel::dszCons(ih,iw,imPtr->m_cs);
		dsmIM->addShadeScrib(cons,1.0);
	}
	if (imPtr->m_isCR)
	{
		Constraint cons = IntrinsicModel::dszCons(ih,iw,imPtr->m_cr);
		dsmIM->addAlbedoScrib(cons,1.0);
	}
	if (imPtr->m_isAbsS)
	{
		Constraint cons = IntrinsicModel::dszCons(ih,iw,imPtr->m_abs);
		dsmIM->addAbsShadeScrib(cons,1.0);
	}
	//resize the mask
	cv::resize(imPtr->m_ROIMask,dsmIM->m_ROIMask,dsmIM->m_ROIMask.size(),0,0,cv::INTER_NEAREST);
	cv::resize(imPtr->m_featureMask,dsmIM->m_featureMask,dsmIM->m_featureMask.size(),0,0,cv::INTER_NEAREST);
	//resize the pixel normal
	cv::resize(imPtr->m_pixNorm,dsmIM->m_pixNorm,  dsmIM->m_pixNorm.size(),0,0,cv::INTER_NEAREST);
	return dsmIM;
}

#endif
