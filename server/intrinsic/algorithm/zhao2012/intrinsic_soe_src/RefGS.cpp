#include "RefGS.h"

RefGS::RefGS(DataManager* dmPtr, std::string gsName) :
	GroupingScheme(dmPtr, gsName) {
}

RefGS::~RefGS() {

}

//void RefGS::saveGrpVis(std::string prefix,std::string gsName){
//	//
//	//sort groups in descend order by their size
//	grpEle_vect grps = m_groups;
//	std::cout<<"# of groups in total:"<< grps.size()<<std::endl;
//	std::sort(grps.begin(),grps.end(),grpSizeGreater);
//	char buffer[256];
//	int grpCnt = (grps.size() > 10? 10 : grps.size());
//	for(int i=0; i< grpCnt;i++){
//		mat_3f canvas = m_dmPtr->getInput().clone();
//		drawGrp(grps[i],canvas);
//		std::string winName(buffer);
//		sprintf(buffer,"%s_%s_%d.png",prefix.c_str(),gsName.c_str(),i);
//		std::string sn(buffer);
//		cv::imwrite(sn,canvas * 255.0);
//	}
//	std::string winName(buffer);
//	sprintf(buffer,"%s_%s_allGrps_.png",prefix.c_str(),gsName.c_str());
//	mat_3f canvas =	drawAllGrp();
//	std::string sn(buffer);
//	cv::imwrite(sn,canvas * 255.0);
//}

void RefGS::getGrpChrom(){
	//
	DataManager& dm = *m_dmPtr;
	mat_3f& chromImg = dm.getChrom();
	cv::Size imgSize = dm.getImgSize();
	m_grpChromVect.clear();
	for (int i=0; i<m_groups.size(); i++) {
		GrpEle& ge = m_groups[i];
		cv::Vec3f avgChrom = 0;
		int grpSize = ge.m_eMember.size();
		for (int j=0; j<grpSize; j++) {
			Element& ele = ge.m_eMember[j];
			int pixID = ele.m_eleID;
			int x = pixID % imgSize.width;
			int y = pixID / imgSize.width;
			cv::Vec3f& chrom = chromImg(y, x);
			avgChrom += chrom;
		}
		float norm = cv::norm(avgChrom);
		norm = norm>1e-8?1/norm:0;
		avgChrom[0] *= norm;
		avgChrom[1] *= norm;
		avgChrom[2] *= norm;
//		std::cout<<cv::norm(avgChrom)<<std::endl;
//		getchar();
		m_grpChromVect.push_back(avgChrom);
	}
}
void RefGS::getGrpMaxInt() {
	//
	DataManager& dm = *m_dmPtr;
	mat_3f& inputImg = dm.getInput();
	cv::Size imgSize = dm.getImgSize();
	m_grpMaxIntensity.clear();
	for (int i=0; i<m_groups.size(); i++) {
		GrpEle& ge = m_groups[i];
		float maxInt = -1;
		for (int j=0; j<ge.m_eMember.size(); j++) {
			Element& ele = ge.m_eMember[j];
			int pixID = ele.m_eleID;
			int x = pixID % imgSize.width;
			int y = pixID / imgSize.width;
			cv::Vec3f& rgb = inputImg(y, x);
			float pixInt = cv::norm(rgb);
			if (pixInt > maxInt) {
				maxInt = pixInt;
			}
		}
		m_grpMaxIntensity.push_back(maxInt);
	}
}

void RefGS::drawGrp(GrpEle& ge, mat_3f& canvas){
	int w = canvas.size().width;
	Element& ele0 = ge.m_eMember[0];
	int px0 = ele0.m_eleID % w;
	int py0 = ele0.m_eleID / w;
	float r = rand()/(RAND_MAX + 1.0);
	float g = rand()/(RAND_MAX+1.0);
	float b = rand()/(RAND_MAX+1.0);
	
	for (int j=0; j<ge.m_eMember.size(); j++) {
		Element& ele = ge.m_eMember[j];
		int px = ele.m_eleID % w;
		int py = ele.m_eleID / w;
		cv::rectangle(canvas,cv::Point(px-2,py-2),cv::Point(px+2,py+2),cv::Scalar(b,g,r),1,CV_AA);
	}	
}

void RefGS::_grpProperty(int gID,int index, float& shading, float& reflectance){
	//
	DataManager& dm = *m_dmPtr;
	float grpMaxInt = m_grpMaxIntensity[gID];
//	std::cout<<"base:"<<m_base<<std::endl;
	reflectance = grpMaxInt * MRF_LABEL_NUM /(index + m_base);
}

void RefGS::_setSoution(int grpID, int eleID, int solution, float& shading) {
	// solution is shading index
	DataManager& dm = *m_dmPtr;
	mat_3f& inputImg = dm.getInput();
	cv::Size imgSize = inputImg.size();
	int eX = eleID % imgSize.width;
	int eY = eleID / imgSize.width;
	cv::Vec3f& rgb = inputImg(eY, eX);
	float pixInt = cv::norm(rgb);
	float grpMaxInt = m_grpMaxIntensity[grpID];
	float a = grpMaxInt * MRF_LABEL_NUM;
	a = a > 1e-8? pixInt/a: 0;
	shading = a * (m_base + solution);
}

void RefGS::_eleProperty(int gID, int eleID, int index, float& shading,
		float& reflectance) {
	// solution is shading index
	DataManager& dm = *m_dmPtr;
	mat_3f& inputImg = dm.getInput();
	cv::Size imgSize = inputImg.size();
	int eX = eleID % imgSize.width;
	int eY = eleID / imgSize.width;
	cv::Vec3f& rgb = inputImg(eY, eX);
	
	float pixInt = cv::norm(rgb);
	float grpMaxInt = m_grpMaxIntensity[gID];
	float a = grpMaxInt * MRF_LABEL_NUM;
	a = (a > 1e-8? pixInt/a: 0);
	shading = a * (m_base + index);
	reflectance = (shading > 1e-8? pixInt/shading: 0);
	
}

