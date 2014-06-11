#include "PixelNormGS.h"
#include <vector>
#include "Utility.h"
#include "AppConfig.h"
#include "ANNCluster.h"


PixelNormGS::PixelNormGS(DataManager* dmPtr, mat_3f normImg, mat_u mask) :
	ShadingGS(dmPtr, "3d normal grouping sheme"), m_3dNormImg(normImg),
			m_mask(mask)

{
	
}


PixelNormGS::~PixelNormGS() {

}

mat_3f PixelNormGS::drawMask() {
	mat_3f canvas = m_dmPtr->getInput().clone();
	for (int i=0; i<canvas.size().height; i++)
		for (int j=0; j<canvas.size().width; j++) {
			if (m_mask(i, j))
				canvas(i, j) = cv::Vec3f(1,1,1);
		}
	//
	return canvas;
}

bool GrpSizeGrt(const GrpEle& ge1 ,const GrpEle& ge2){
	return ge1.m_eMember.size() > ge2.m_eMember.size();
}

void PixelNormGS::GrpMozac(std::string basePath){
	
	grpEle_vect grpBk = m_groups;
	std::sort(grpBk.begin(),grpBk.end(),GrpSizeGrt);

	int patchCnt = 0;
	for (int i = 0; i < grpBk.size(); i++)
	{
		if (grpBk[i].m_eMember.size() > 1)
		{
			patchCnt ++;
		}
		
	}
	
	int vPSize= m_dmPtr->getImgSize().height;
	int hPSize = m_dmPtr->getImgSize().width;
	int sep = 2;
	int hCnt = 5;
	int vCnt = patchCnt / hCnt +1;
	if(vCnt > 5)
		vCnt = 5;

	mat_3f canvas(vCnt * (vPSize + sep), hCnt * (hPSize + sep));
	//
	int pIndex = 0;

	int canvasCnt = 0;
	mat_3f input = m_dmPtr->getInput();
	mat_3f patchCanvas = input.clone();

	canvas = cv::Vec3f(0,0,0);

	char buffer[256];
	for (int i = 0; i <= patchCnt; i++)
	{
		
		if (pIndex >= hCnt * vCnt || i == patchCnt)
		{
			//save this canvas
			sprintf(buffer,"%s/ngs_%06d.png",basePath.c_str(),canvasCnt++);
			cv::imwrite(std::string(buffer),canvas * 255.0);
			pIndex = 0;
			canvas = cv::Vec3f(0,0,0);
			if (  i == patchCnt)
			{
				break;
			}
			
		}
	
		input.copyTo(patchCanvas);
		patchCanvas = cv::Vec3f(0,0,0);
		drawGrp(grpBk[i],patchCanvas); //draw the normals
		cv::imshow("pc",patchCanvas);
		cv::waitKey(0);
		int pr = pIndex / hCnt;
		int pc = pIndex % hCnt;
		int lx = pc * (sep + hPSize);
		int ty = pr * (sep + vPSize);
		for (int k = 0; k < vPSize; k++)
		{
			for (int l = 0; l < hPSize; l++)
			{
				canvas(ty + k, lx + l) = patchCanvas( k,l);
			}
			
		}
		pIndex ++;
	}
	
}

void PixelNormGS::drawGrp(GrpEle& ge, mat_3f& canvas) {
	//show pixel 3d normals using RGB
	DataManager& dm = *m_dmPtr;
	cv::Size imgSize = dm.getImgSize();
	if (ge.m_eMember.size() < 2)
		return;
	Element& ele = ge.m_eMember[0];

	//int x0 = ele.m_eleID % imgSize.width;
	//int y0 = ele.m_eleID / imgSize.width;

	float r = rand()/(RAND_MAX + 1.0);
	float g = rand()/(RAND_MAX+1.0);
	float b = rand()/(RAND_MAX+1.0);

	//float r = 1.0;
	//float g = 1.0;
	//float b = 1.0;

	cv::Vec3f grpColor(r,g,b);

	for (int i=0; i<ge.m_eMember.size(); i++) {
		Element& ele = ge.m_eMember[i];
		int x = ele.m_eleID % imgSize.width;
		int y = ele.m_eleID / imgSize.width;
		//cv::Vec3f pix3dNorm = this->m_3dNormImg(y0, x0);
		//pix3dNorm[0] = (pix3dNorm[0] + 1)/2;
		//pix3dNorm[1] = (pix3dNorm[1] + 1)/2;
		//pix3dNorm[2] = (pix3dNorm[2] + 1)/2;
		
#ifdef __ANN_GRP__
		//canvas(y,x) = grpColor; //
		cv::rectangle(canvas, cv::Point(x-2, y-2), cv::Point(x+2, y+2),
			cv::Scalar(r,g,b), 1, CV_AA);

#else
		cv::rectangle(canvas, cv::Point(x-2, y-2), cv::Point(x+2, y+2),
				cv::Scalar(pix3dNorm[0], pix3dNorm[1], pix3dNorm[2]), 1, CV_AA);
#endif
	}
}

void PixelNormGS::_group() {
	cv::Size imgSize = m_3dNormImg.size();
	std::vector<int> pixIDVect;
	for (int i=0, pixID = 0; i<imgSize.height; i++) {
		for (int j=0; j<imgSize.width; j++, pixID++) {
			if (m_mask(i, j)) {
				pixIDVect.push_back( j + i * imgSize.width );
			}
		}
	}
	//std::cout << "# of nv:" << pixIDVect.size() << std::endl;
	//cv::imshow("norm",m_3dNormImg);
	//cv::waitKey(0);
	int pnCnt = pixIDVect.size();
#ifdef __ANN_GRP__
	mat_f nMat(pnCnt, 3); //
	for (int i = 0; i < pnCnt; i++) {
		int y = pixIDVect[i] / imgSize.width;
		int x = pixIDVect[i] % imgSize.width;
		float nx = m_3dNormImg(y,x)[0];
		float ny = m_3dNormImg(y,x)[1];
		float nz = m_3dNormImg(y,x)[2];
		nMat(i, 0) = m_3dNormImg(y,x)[0];
		nMat(i, 1) = m_3dNormImg(y,x)[1];
		nMat(i, 2) = m_3dNormImg(y,x)[2];
	}
#endif
	//	std::cout<<"# of pixels having 3d norm:"<<pixIDVect.size()<<std::endl;
#ifdef __ANN_GRP__
	ANNCluster ac;
	float radius = AppConfig::m_normChange_trd * AppConfig::m_normChange_trd;
	ac.doCluster(nMat, m_groups, radius);
	//
	for (int i = 0; i < m_groups.size(); i++) {
		GrpEle& ge= m_groups[i];
		ge.m_grpType = SHADE;
		for (int j = 0; j < ge.m_eMember.size(); j++) {
			Element& ele = ge.m_eMember[j];
			ele.m_eleID = pixIDVect[ele.m_eleID]; //
		}
	}
	
#else
	
	std::vector<bool> matchedFlag(pixIDVect.size(), false);

	float angleThresh = 0.01;

	for (int i=0, grpId=0; i<pixIDVect.size(); i++) {
		if (matchedFlag[i])
		continue;
		int xi = pixIDVect[i] % imgSize.width;
		int yi = pixIDVect[i] / imgSize.width;
		cv::Vec3f& vi = m_3dNormImg(yi, xi);
		GrpEle ge;
		ge.m_gID = grpId++;
		ge.m_grpType = SHADE; //shading based

		for (int j=0; j<pixIDVect.size(); j++) {
			int xj = pixIDVect[j] % imgSize.width;
			int yj = pixIDVect[j] / imgSize.width;
			cv::Vec3f& vj = m_3dNormImg(yj, xj);
			float dist = Utility::vecDist(vi, vj)/4;

			if (dist < angleThresh) {
				ge.m_eMember.push_back(Element(pixIDVect[j], 1 - dist
								/angleThresh));
				matchedFlag[j] = true;
			}
		}
		m_groups.push_back(ge);
	}
#endif
	m_eleCnt = imgSize.width * imgSize.height;
	//
	_grp2ele();
	int grpID = m_groups.size();
	for (int i=0; i<m_elements.size(); i++) {
		//std::cout <<"element i: " << i << std::endl;
		EleGrp& eg = m_elements[i];
		if (eg.m_gMember.empty()) {
			GrpEle ge;
			ge.m_gID = grpID;
			ge.m_grpType = SHADE;
			ge.m_eMember.push_back(Element(i, 1));
			m_groups.push_back(ge);
			eg.m_gMember.push_back(Element(grpID, 1.0));
			grpID ++;
		}
	}
	m_elements.clear(); //
	
}

void PixelNormGS::_interpolation() {
	//interpolate pixel 3d normal iteratively
	cv::Size imgSize = m_mask.size();
	bool flag = true;
	mat_f pixConf(imgSize);
	pixConf = 0.0;
	for (int i=0; i<imgSize.height; i++)
		for (int j=0; j<imgSize.width; j++) {
			if (m_mask(i, j)) {
				pixConf = 1.0;
			}
		}
	//
	while (flag) {
		bool flag = false; //there are pixels without norm
		for (int i=0; i<imgSize.height; i++)
			for (int j=0; j<imgSize.width; j++) {
				if (!m_mask(i, j)) {
					//not set yet, interpolated from its eight neighbor pixels
					flag = true; //

				}
			}
	}
}
