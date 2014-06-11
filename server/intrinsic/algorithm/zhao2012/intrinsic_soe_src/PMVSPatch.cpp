#if 0
#include "PMVSPatch.h"
#include <boost/filesystem.hpp>
#include <fstream>
#include <iostream>
#include "Utility.h"

namespace bfs = boost::filesystem;

Patch::Patch()
:m_visCnt1(0)
,m_visCnt2(0)
,m_normAvaiable(true)
{
}



mat_3f ViewInfo::visNorm(){
	//
	int ih = m_viewImg.size().height;
	int iw = m_viewImg.size().width;
	mat_3f vis(m_viewImg.size());
	vis = cv::Vec3f(0,0,0);
	for (int i = 0; i < ih; i++)
	{
		for (int j=0; j < iw; j++)
		{
			if (cv::norm(m_pixNorm(i,j)) < 1e-8)
			{
				vis(i,j) = cv::Vec3f(0,0,0);
				continue;
			}
			cv::Vec3f nv = m_pixNorm(i,j);
			nv = nv + cv::Vec3f(1,1,1);
			nv[0] /= 2;
			nv[1] /= 2;
			nv[2] /= 2;
			vis(i,j)[0] = nv[2];
			vis(i,j)[1] = nv[1];
			vis(i,j)[2] = nv[0];
		}
	}
	return vis;
}

void ViewInfo::save(){
	//save the pixel norm visualization
	bfs::path p1(m_viewImgFile);
	bfs::path p2 = p1.branch_path();
	std::string imgName = bfs::basename(p1);
	std::string imgExt = bfs::extension(p1);
	std::string visName = imgName + "_vis";
	std::string visPath = p2.string() + "/" + visName + ".png";
	mat_3f visImg = visNorm();
	//cv::imshow("vis",visImg);
	//cv::waitKey(0);
	visImg *= 255.0;
	cv::imwrite(visPath,visImg);
}


Patch::~Patch(){

}


ViewInfo::ViewInfo()
:m_viewIdx(-1)
,m_centerPos(cv::Vec3f(-1,-1,-1))
,m_ccEstiamted(false)
{


}
void ViewInfo::createStruct(mat_3f img, int viewIdx,std::string viewImgFile){
	m_viewIdx = viewIdx;
	m_viewImgFile = viewImgFile;
	int h = img.size().height;
	int w = img.size().width;
	m_viewImg = img.clone();
	m_pixNorm = mat_3f(h,w);
	m_normMask = mat_u(h,w);
	m_roiMask = mat_u(h,w);
	m_roiMask = 255;
	m_prjMat = mat_f(3,4);
	//////////////////////////////////////////////////////////////////////////
	m_pixNorm = cv::Vec3f(0,0,0);
	m_normMask = 0;
	m_prjMat = 0;
}


void ViewInfo::_estiamteCameraCenter(){
	int ih = m_viewImg.size().height;
	int iw = m_viewImg.size().width;

	//infer the camera center from perspective matrix
	if (!m_ccEstiamted)
	{

		cv::Vec2f v1(0,0),v2(iw - 1, 0),v3( 0 , ih -1 ), v4(iw - 1, ih - 1);
		std::vector<cv::Vec2f> ptVec;
		ptVec.push_back(v1);
		ptVec.push_back(v2);
		ptVec.push_back(v3);
		ptVec.push_back(v4);
		//
		m_centerPos = convergePoint(m_prjMat,ptVec);
		m_ccEstiamted = true;
	}

}

bool theSameSide(cv::Vec3f p1,cv::Vec3f p2, cv::Vec3f v1, cv::Vec3f v2){
	//
	cv::Vec3f v3 = v2 - v1;
	cv::Vec3f v4 = p1 - v1;
	cv::Vec3f v5 = p2 - v1;
	//
	cv::Vec3f prod1 = v3.cross(v4);
	cv::Vec3f prod2 = v3.cross(v5);
	float dProd = prod1.ddot(prod2);
	if (dProd >= 0)
	{
		return true;
	}
	else{
		return false;
	}
}

bool insideTriangle(cv::Vec2f p11, cv::Vec2f p1, cv::Vec2f p2, cv::Vec2f p3){
	cv::Vec3f p = cv::Vec3f(p11[0],p11[1],0);
	cv::Vec3f a = cv::Vec3f(p1[0],p1[1],0);
	cv::Vec3f b = cv::Vec3f(p2[0],p2[1],0);
	cv::Vec3f c = cv::Vec3f(p3[0],p3[1],0);
	if (theSameSide(p,a,b,c) && theSameSide(p,b,a,c) && theSameSide(p,c,a,b))
	{
		return true;
	}
	else{
		return false;
	}
}


float triangleArea(float a, float b, float c){
	//Heron's formula
	float s = (a + b + c) * 0.5;
	return sqrt(s * (s - a) * (s - b) * (s - c));
}

void ViewInfo::interplation(){
	//do interplation
//	vertexSet vSet;
//	int iw = m_viewImg.size().width;
//	int ih = m_viewImg.size().height;
//	for (int i = 0; i < ih; i++)
//	{
//		for (int j = 0; j < iw; j++)
//		{
//			if (m_normMask(i,j))
//			{
//				//
//				vSet.insert(vertex(j,i));
//			}
//		}
//	}
//	//now compute the delaunay
//	Delaunay del;
//	triangleSet trgs;
//	del.Triangulate(vSet,trgs);
//	std::cout << "3d normal interpolation by Delaunay triangulation" << std::endl;
//	std::cout << "# of triangles:" << trgs.size() << std::endl;
//	//
//	ctIterator iter;
//	cv::Vec2f vArry[3];
//	cv::Vec3f nrArry[3];
//	for (iter = trgs.begin(); iter != trgs.end(); iter++)
//	{
//		//compute the triangle side length
//		float minX = iw, maxX = -1, minY = ih, maxY = -1;
//
//		for (int j = 0; j < 3; j++)
//		{
//			const vertex* tmpV = iter->GetVertex(j);
//			int x = tmpV->GetX();
//			int y = tmpV->GetY();
//			vArry[j] = cv::Vec2f(x,y);
//			nrArry[j] = m_pixNorm(y,x); //get the pixel normal
//			if (x < minX)
//			{
//				minX = x;
//			}
//			if (x > maxX)
//			{
//				maxX = x;
//			}
//			if (y < minY)
//			{
//				minY = y;
//			}
//			if (y > maxY)
//			{
//				maxY = y;
//			}
//		}
//		//
//		float a = cv::norm(vArry[0] - vArry[1]);
//		float b = cv::norm(vArry[1] - vArry[2]);
//		float c = cv::norm(vArry[2] - vArry[0]);
//
//		//discard triangle with large side length
//		if (a > 11 || b > 11 || c > 11)
//		{
//			continue;
//		}
//		//discard triangle with different normals
//		float pd1 = nrArry[0].ddot(nrArry[1]);
//		float pd2 = nrArry[0].ddot(nrArry[2]);
//
//		if (pd1 < 0.90 || pd2 < 0.90)
//		{
//			continue;
//		}
//
//
//		//for each triangle, fill the pixel inside
//		for (int y = minY; y <= maxY; y++)
//		{
//			for (int x = minX; x <= maxX; x++)
//			{
//				cv::Vec2f p(x,y);
//				if (insideTriangle(p,vArry[0],vArry[1],vArry[2]))
//				{
//					//
//					float dist1 = cv::norm(p - vArry[0]);
//					float dist2 = cv::norm(p - vArry[1]);
//					float dist3 = cv::norm(p - vArry[2]);
//					float ws = 1 / (dist1 + dist2 + dist3);
//					float w1 = dist1 * ws;
//					float w2 = dist2 * ws;
//					float w3 = dist3 * ws;
//					cv::Vec3f iv;
//					iv[0] = nrArry[0][0] * w1 + nrArry[1][0] * w2 + nrArry[2][0] * w3;
//					iv[1] = nrArry[0][1] * w1 + nrArry[1][1] * w2 + nrArry[2][1] * w3;
//					iv[2] = nrArry[0][2] * w1 + nrArry[1][2] * w2 + nrArry[2][2] * w3;
//					//std::cout << "interp..." << std::endl;
//					m_pixNorm(y,x) = iv;
//					//m_normMask(y,x) = 255;
//				}
//			}
//		}
//	}
//	//////////////////////////////////////////////////////////////////////////
//	std::cout << "done..." << std::endl;
}

void ViewInfo::applyMask(){
	//
	int h = m_viewImg.size().height;
	int w = m_viewImg.size().width;

	int x1 = w, y1 = h ,x2 = -1, y2 = -1;

	for (int i = 0; i < h; i++)
	{
		for (int j = 0; j < w; j++)
		{
			if (m_roiMask(i,j))
			{
				if (i < y1)
				{
					y1 = i;
				}
				if (i > y2)
				{
					y2 = i;
				}
				if (j < x1)
				{
					x1 = j;
				}
				if (j > x2 )
				{
					x2 = j;
				}
			}
		}
	}
	int w1 = x2 - x1 + 1;
	int h1 = y2 - y1 + 1;
	//apply the roi to the norm image and input image
	mat_3f viewImg(h1,w1);
	mat_3f normImg(h1,w1);
	mat_u nmImg(h1,w1);
	for (int i = y1; i <= y2; i++)
	{
		for (int j = x1; j <= x2; j++)
		{
			viewImg(i - y1,j - x1) = m_viewImg(i,j);
			normImg(i - y1,j - x1) = m_pixNorm(i,j);
			nmImg(i - y1, j - x1) = m_normMask(i,j);
		}
	}
	m_viewImg = viewImg;
	m_normMask = nmImg;
	m_pixNorm = normImg;
	m_roiMask = mat_u(h1,w1);
	m_roiMask = 255;
	//cv::imshow("roiImg",m_viewImg);
	//cv::imshow("normVis",visNorm());
	//cv::waitKey(0);
}

void ViewInfo::projectPatch(std::vector<Patch>& patchList){
	//project each patch's normal to the image plane

	_estiamteCameraCenter();
	int ih = m_viewImg.size().height;
	int iw = m_viewImg.size().width;

	mat_f homoVec(4,1);
	homoVec(3,0) = 1.0;

	std::cout << "# of patches to project:" << patchList.size() << std::endl;
	for (int i = 0; i < patchList.size(); i++)
	{
		Patch& pch = patchList[i];
		if (pch.m_normAvaiable&& pch.m_visFlag[m_viewIdx])
		{
			//project current patch
			homoVec(0,0) = pch.m_pt[0];
			homoVec(1,0) = pch.m_pt[1];
			homoVec(2,0) = pch.m_pt[2];
			mat_f imgPos = m_prjMat * homoVec;
			imgPos(2,0) = imgPos(2,0) > 1e-8 ? 1 / imgPos(2,0) : 0;
			imgPos(0,0) *= imgPos(2,0);
			imgPos(1,0) *= imgPos(2,0);
			int px = floor(imgPos(0,0));
			int py = floor(imgPos(1,0));

			if (py < 0 || py > ih || px < 0 || px > iw)
			{
				continue;
			}

			//correct the normal direction 
			cv::Vec3f& ptNorm = pch.m_norm;
			cv::Vec3f viewVec = m_centerPos - pch.m_pt;
			if (ptNorm.ddot(viewVec) < 0)
			{
				ptNorm = cv::Vec3f(0,0,0) - ptNorm;
			}
			m_pixNorm(py,px) += ptNorm;
			m_normMask(py,px) = 255;
			//for (int k1 = -1; k1 <= 1; k1++)
			//{
			//	for (int k2 = -1; k2 <= 1; k2++)
			//	{
			//		int x1 = px + k2;
			//		int y1 = py + k1;
			//		if (x1 < 0 || x1 >= iw || y1 < 0 || y1 >= ih)
			//		{
			//			continue;
			//		}
			//		//now correct the normal direction
			//		m_pixNorm(y1,x1) += pch.m_norm;
			//		m_normMask(y1,x1) = 255;
			//	}
			//}
		}
	}
	//interplation();
	for (int i = 0; i < ih ;i++)
	{
		for (int j = 0; j < iw; j++)
		{
			if (m_normMask(i,j))
			{
				cv::Vec3f& pn = m_pixNorm(i,j);
				float nr = cv::norm(pn);
				nr = nr > 1e-8 ? 1/nr: nr;
				pn[0] *= nr;
				pn[1] *= nr;
				pn[2] *= nr;
			}
		}
	}
	
}

ViewInfo::~ViewInfo(){

}


PMVS2::PMVS2(std::string pmvsRootPath)
:m_pmvsRootPath(pmvsRootPath){
	m_txtPath = m_pmvsRootPath + "txt/";
	m_visPath = m_pmvsRootPath + "visualize/";
	m_modelPath = m_pmvsRootPath + "models/";
	//
	_init();
}


void PMVS2::_getViewCnt(){
	std::vector<std::string> m_viewImgFile;
	Utility::findFilexByExt(m_visPath,".jpg",m_viewImgFile);
	m_viewCnt = m_viewImgFile.size();
}

void PMVS2::_init(){
	_getViewCnt();
	std::cout << "# of views:" << m_viewCnt << std::endl;
	//reserve space
	std::cout << "init view information" << std::endl;
	for (int i = 0; i < m_viewCnt; i++)
	{
		m_viewInfo.push_back(ViewInfo());
	}

	//load the matrix
	std::cout << "load camera parameters" << std::endl;
	_loadCamMatrix();
	//load ply and .patch files
	std::cout << "load 3d information" << std::endl;
	_loadModel();
	//
}

void PMVS2::_loadCamMatrix(){
	char buffer[512];
	std::fstream camFS;
	std::string line;
	mat_f camMat(3,4);
	for (int i = 0; i < m_viewCnt; i++)
	{
		sprintf(buffer,"%s%04d.txt",m_txtPath.c_str(),i);
		//std::cout << buffer << std::endl;
		camFS.open(buffer,std::ios_base::in);
		assert(camFS.good());
		camFS >> line;
		for (int j = 0; j < 3; j++)
		{
			for (int k = 0; k < 4; k++)
			{
				camFS >> camMat(j,k);
#ifdef __DUMP_FILE__
				std::cout << camMat(j,k) << " ";
#endif
			}
#ifdef __DUMP_FILE__
			std::cout << std::endl;
#endif
		}
		m_camParaList.push_back(camMat.clone());
		camFS.close();
	}
	std::cout << "# of matrix loaded:" << m_viewCnt << std::endl;
	//////////////////////////////////////////////////////////////////////////
}

void PMVS2::loadViewInfo(int viewIdx ){

	if (viewIdx == -1)
	{
		for (int i = 0; i < m_viewCnt; i++)
		{
			loadViewInfo(i);
		}
	}
	else{
		char buffer[512];
		sprintf(buffer,"%s%04d.jpg",m_visPath.c_str(),viewIdx);
		//std::cout << buffer << std::endl;
		mat_3f img = cv::imread(buffer) / 255.0;
#ifdef __DUMP_FILE__
		cv::imshow("viewImg",img);
		cv::waitKey(0);
#endif
		int ih = img.size().height;
		int iw = img.size().width;
		ViewInfo vi;
		vi.createStruct(img,viewIdx,buffer);
		vi.m_prjMat = m_camParaList[viewIdx];
		m_viewInfo[viewIdx] = vi;
		//project the patches to image plane
		m_viewInfo[viewIdx].projectPatch(m_patchList);
		///read the mask file
		sprintf(buffer,"%s%04d_msk.png",m_visPath.c_str(),viewIdx);
		if (bfs::exists(buffer))
		{
			mat_u mskImg = cv::imread(buffer,CV_LOAD_IMAGE_GRAYSCALE);
			//cv::imshow("roimsk",mskImg);
			//cv::waitKey(0);
			m_viewInfo[viewIdx].setMask(mskImg);
			m_viewInfo[viewIdx].applyMask();
		}

	}
}

//
//void PMVS2::doProjection(){
//	for (int i = 0; i < m_viewCnt; i++)
//	{
//		std::cout << "project patches to view:" << i << std::endl;
//		ViewInfo& vi = m_viewInfo[i];
//		vi.projectPatch(m_patchList);
//		vi.save();
//		//std::cout << "show norm" << std::endl;
//		//cv::imshow("norm",vi.visNorm());
//		//cv::waitKey(0);
//	}
//}

void PMVS2::_saveEstimatedNormalAsPly(){
	//
	std::string folder = m_modelPath + "/est";
	if (!bfs::exists(folder))
	{
		bfs::create_directories(folder);
	}
	std::string plyFile = folder + "/estNorm.ply";
	std::fstream plyFS;
	plyFS.open(plyFile.c_str(),std::ios::out);
	plyFS << "ply\n";
	plyFS << "format ascii 1.0\n";
	plyFS << "element vertex " << m_patchList.size() << "\n";
	plyFS << "property float x\n";
	plyFS << "property float y\n";
	plyFS << "property float z\n";
	plyFS << "property float nx\n";
	plyFS << "property float ny\n";
	plyFS << "property float nz\n";
	plyFS << "property uchar red\n";
	plyFS << "property uchar green\n";
	plyFS << "property uchar blue\n";
	plyFS << "property uchar alpha\n";

	plyFS << "element face 0\n";
	plyFS << "property list uchar int vertex_indices\n";
	plyFS << "end_header\n";

	for (int i = 0; i < m_patchList.size(); i++)
	{
		Patch& pch = m_patchList[i];
		plyFS << 
			pch.m_pt[0] << " " << pch.m_pt[1] << " " << pch.m_pt[2] << " "
			<< pch.m_norm[0] << " " << pch.m_norm[1] << " " << pch.m_norm[2] << " " 
			<< (int)pch.m_r << " " << (int)pch.m_g << " " << (int)pch.m_b << " " << 255 << "\n";
	}
	plyFS << std::endl;
	plyFS.close();
}

void PMVS2::_loadModel(){
	std::vector<std::string> modelFiles;
	Utility::findFilexByExt(m_modelPath,".patch",modelFiles);
	if (modelFiles.empty())
	{
		std::cout << "patch file not found" << std::endl;
	}
	else{
		m_patchFile = modelFiles[0];
	}
	modelFiles.clear();
	Utility::findFilexByExt(m_modelPath,".ply",modelFiles);
	if (modelFiles.empty())
	{
		std::cout << "patch file not found" << std::endl;
	}
	else{
		m_plyFile = modelFiles[0];
	}

	modelFiles.clear();
	Utility::findFilexByExt(m_modelPath,".pset",modelFiles);
	if (modelFiles.empty())
	{
		std::cout << "patch file not found" << std::endl;
	}
	else{
		m_ptFile = modelFiles[0];
	}

	//
	_loadPatch();
	//
	//_loadPly();
	////
	_estimateNormal();
	_saveEstimatedNormalAsPly();
	//////////////////////////////////////////////////////////////////////////
}


void PMVS2::_estimateNormal(){
	//
	NormalEstimator ne;
	std::vector<cv::Vec3f> ptList;
	for (int i = 0; i < m_patchList.size(); i++)
	{
		Patch& pch = m_patchList[i];
		ptList.push_back(pch.m_pt);
	}
	ne.specifyPointSet(ptList);
	ne.fitNormal();
	for (int i = 0; i < m_patchList.size(); i++)
	{
		m_patchList[i].m_normAvaiable = ne.m_ptNormFlag[i];
		m_patchList[i].m_norm = ne.m_ptNorm[i];
	}
	
	//
	//now update the normal
	//for (int i = 0; i < m_patchList.size(); i++)
	//{
	//	cv::Vec3f v2 = ne.m_ptNorm[i];
	//	if (ne.m_ptNormFlag[i])
	//	{
	//		//correct the direction
	//		cv::Vec3f v1 = m_patchList[i].m_norm;
	//		float pd1 = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2];
	//		//float pd2 = v1.ddot(cv::Vec3f(0,0,0) - v2);
	//		if (pd1 < 0)
	//		{
	//			v2 = cv::Vec3f(0,0,0) - v2;
	//		}
	//	}
	//	m_patchList[i].m_norm = v2;
	//}
	//
}

mat_f ViewInfo::eqMatFromImgPt(mat_f& prjMat, cv::Vec2f& imgPt){
	//
	float u = imgPt[0];
	float v = imgPt[1];
	mat_f lMat(2, 4);

	lMat(0, 0) = prjMat(2, 0)*u - prjMat(0, 0);
	lMat(0, 1) = prjMat(2, 1)*u - prjMat(0, 1);
	lMat(0, 2) = prjMat(2, 2)*u - prjMat(0, 2);

	lMat(1, 0) = prjMat(2, 0)*v - prjMat(1, 0);
	lMat(1, 1) = prjMat(2, 1)*v - prjMat(1, 1);
	lMat(1, 2) = prjMat(2, 2)*v - prjMat(1, 2);

	lMat(0, 3) = -prjMat(0, 3) + prjMat(2, 3)*u;
	lMat(1, 3) = -prjMat(1, 3) + prjMat(2, 3)*v;

	return lMat;
}
cv::Vec3f ViewInfo::convergePoint(mat_f& prjMat, std::vector<cv::Vec2f>& ptSeq){
	//
	int ptCnt = ptSeq.size();
	mat_f lMat(2*ptCnt, 3), rMat(2*ptCnt, 1);
	for (int i=0; i<ptCnt; i++) {
		mat_f eqM = eqMatFromImgPt(prjMat, ptSeq[i]);
		lMat(i*2, 0) = eqM(0, 0);
		lMat(i*2, 1) = eqM(0, 1);
		lMat(i*2, 2) = eqM(0, 2);
		lMat(i*2+1, 0) = eqM(1, 0);
		lMat(i*2+1, 1) = eqM(1, 1);
		lMat(i*2+1, 2) = eqM(1, 2);
		rMat(i*2, 0) = -eqM(0, 3);
		rMat(i*2+1, 0) = -eqM(1, 3);
	}
	mat_f x(3, 1);
	cv::solve(lMat, rMat, x, cv::DECOMP_SVD);
	return cv::Vec3f(x(0, 0), x(1, 0), x(2, 0));
}


ViewInfo& PMVS2::getViewInfo(int viewIdx){
	if (viewIdx < 0 || viewIdx >= m_viewCnt)
	{
		viewIdx = 0;
	}
	return m_viewInfo[viewIdx];
}


void PMVS2::deleteViewInfo(int idx ){
	if (idx == -1)
	{
		for (int i = 0; i < m_viewCnt; i++)
		{
			deleteViewInfo(i);
		}
	}
	else{
		m_viewInfo[idx] = ViewInfo();
	}

}
void PMVS2::_loadPly(){
	std::fstream plyFS;
	plyFS.open(m_plyFile.c_str(),std::ios_base::in);
	assert(plyFS.good());
	std::string line;
	char buffer[512];
	plyFS.getline(buffer,512);
	//std::cout << buffer;
	plyFS.getline(buffer,512);
	//std::cout << buffer;
	plyFS.getline(buffer,512);
	//std::cout << buffer;

	int vertNum;
	plyFS >> line;
	plyFS >> line;
	plyFS >> vertNum;
	std::cout << "# of vertex:" << vertNum << std::endl;
	assert(vertNum == m_patchList.size());
	
	for (int i = 0; i < 15; i++)
	{
		plyFS.getline(buffer,512);
		//std::cout << buffer << std::endl;
	}

	float x,y,z,nx,ny,nz;
	float r,g,b, alpha;

	for (int i = 0; i < vertNum; i++)
	{
		plyFS >> x >> y >> z >> nx >> ny >> nz >> r >> g >> b >> alpha;
		//std::cout << x << " " << y << " " << z << " " << nx << " " << ny << " " << nz << " " << r << " " << g << " " << b << " " << alpha << std::endl;
		//getchar();
		Patch& pch = m_patchList[i];
		pch.m_norm = cv::Vec3f(nx,ny,nz);
		pch.m_r = r;
		pch.m_g = g;
		pch.m_b = b;
	}
	plyFS.close();
	//
}


void PMVS2::_loadPatch(){
	assert(bfs::exists(m_patchFile));
	std::fstream patchFS;
	patchFS.open(m_patchFile.c_str(),std::ios_base::in);
	assert(patchFS.good());
	std::string line;
	int ptCnt;
	patchFS >> line; //PATCHES
	patchFS >> ptCnt; //# of patches
	float x, y ,z , nx , ny , nz;
	float dummy;
	int visCnt1,visCnt2, visIdx;

	std::vector<bool> visFlag(m_viewCnt,false);

	for (int i = 0; i < ptCnt; i++)
	{
		Patch p;
		p.m_visFlag = visFlag;
		patchFS >> line; //PATCHES
		//std::cout << line << std::endl;
		patchFS >> p.m_pt[0] >> p.m_pt[1] >> p.m_pt[2] >> dummy;
	
		patchFS >> p.m_norm[0] >> p.m_norm[1] >> p.m_norm[2] >> dummy;

		patchFS >> p.m_photoConsistency >> p.m_debug1 >> p.m_debug2;
		patchFS >> p.m_visCnt1;
		if (p.m_photoConsistency < 0)
		{
			continue;
		}
		for (int j = 0; j < p.m_visCnt1; j++)
		{
			patchFS >> visIdx;
			p.m_visIndex1.push_back(visIdx);
			p.m_visIndex.insert(visIdx);
			p.m_visFlag[visIdx] = true;
		}
		patchFS >> p.m_visCnt2;

		for (int j = 0; j < p.m_visCnt2; j++)
		{
			patchFS >> visIdx;
			p.m_visIndex2.push_back(visIdx);
			p.m_visIndex.insert(visIdx);
			//p.m_visFlag[visIdx] = true;
		}
		//patchFS >> line; //empty line

#ifdef __DUMP_FILE__
		std::cout << p.m_pt[0] << " " << p.m_pt[1] << " " << p.m_pt[2] << std::endl; 
		std::cout << p.m_norm[0] << " " << p.m_norm[1] << " " << p.m_norm[2] << std::endl; 
		std::cout << p.m_photoConsistency << " " << p.m_debug1 << " " << p.m_debug2 << std::endl;
		std::cout << p.m_visCnt1 << " " << p.m_visCnt2 << std::endl;
		getchar();
#endif
		m_patchList.push_back(p);
	}
	//////////////////////////////////////////////////////////////////////////
	patchFS.close();
	std::cout <<"# of patches loaded:" << m_patchList.size() << std::endl;
}

PMVS2::~PMVS2(){

}
#endif
