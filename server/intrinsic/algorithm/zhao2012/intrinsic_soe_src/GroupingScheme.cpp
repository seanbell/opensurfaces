#include "GroupingScheme.h"

void GroupingScheme::_grp2ele() {
#ifndef __OPT_DEBUG__
	m_elements.clear();
	m_elements = std::vector<EleGrp>(m_eleCnt);
	for(int i=0; i<m_elements.size();i++) {
		m_elements[i].m_eID = i;
	}
	for(int i=0; i< m_groups.size(); i++) {
		GrpEle& ge = m_groups[i];
		int gId = ge.m_gID;
		for(int j=0; j<ge.m_eMember.size();j++) {
			Element& ele = ge.m_eMember[j];
			m_elements[ele.m_eleID].m_gMember.push_back(Element(gId,ele.m_conf));
		}
	}
	//
	
#endif
}

void GroupingScheme::_sortNode() {
#ifndef __OPT_DEBUG__
	for (int i = 0; i < m_groups.size(); i++) {
		GrpEle& ge = m_groups[i];
		std::sort(ge.m_eMember.begin(), ge.m_eMember.end(), EleGreater());
	}
	for (int i = 0; i < m_elements.size(); i++) {
		EleGrp& ge = m_elements[i];
		std::sort(ge.m_gMember.begin(), ge.m_gMember.end(), EleGreater());
	}
#endif
}

bool grpSizeGreater(const GrpEle& ge1, const GrpEle& ge2) {
	return ge1.m_eMember.size() > ge2.m_eMember.size();
}

void GroupingScheme::_setMaxGrpIdx(){
	//for each element, find its shading and reflectance group with maximum confidence
	for (int i=0; i<m_elements.size(); i++) {
		EleGrp& eg = m_elements[i];
		eg.m_mcRefGrpIdx = eg.m_mcShadingGrpIdx = -1;  //undefined yet
		eg.m_mcRefVectPos = eg.m_mcShadingVectPos = -1;// 
		bool sDone = false, rDone = false;
		for (int j=0; j<eg.m_gMember.size(); j++) {
			GrpEle& ge = m_groups[eg.m_gMember[j].m_eleID];
			if (ge.m_gID != eg.m_gMember[j].m_eleID) {
				std::cout<<"inconsistnecy detected"<<std::endl;
			}
			if (ge.m_grpType == SHADE && !sDone) {
				eg.m_mcShadingGrpIdx = ge.m_gID;
				eg.m_mcShadingVectPos = j;
				sDone = true;
			}
			if (ge.m_grpType == REF && !rDone) {
				eg.m_mcRefGrpIdx = ge.m_gID;
				eg.m_mcRefVectPos = j;
				rDone = true;
			}
			if (sDone && rDone)
				break;
		}
	}
}

void GroupingScheme::removeGrpOverlap(){
	//each element is only assigned to one group
	grpEle_vect grps;
	int grpId = 0;
	for (int i = 0; i < m_groups.size(); i++)
	{
		GrpEle& ge = m_groups[i];
		if (ge.m_eMember.size() < 2)
		{
			continue;
		}
		GrpEle newGrp = ge;
		newGrp.m_eMember.clear();
		//check each element of current group whether current group has the maximum confidence amoung the element's group list
		for (int j = 0; j < ge.m_eMember.size(); j++)
		{
			Element& ele = ge.m_eMember[j];
			EleGrp& eg = m_elements[ele.m_eleID]; //
			if (eg.m_gMember[0].m_eleID == ge.m_gID)
			{
				newGrp.m_eMember.push_back(ele); //keep current element
			}
			
		}
		if (newGrp.m_eMember.size() > 1)
		{
			newGrp.m_gID = grpId++;
			grps.push_back(newGrp);
		}
	}
	m_groups = grps;
	//std::cout << " # of grps: " << m_groups.size()<< std::endl;

}

void GroupingScheme::printGrps(std::string fileName) {
	//
	FILE* fid = fopen(fileName.c_str(), "w");
	for (int i=0; i<m_groups.size(); i++) {
		GrpEle& eg = m_groups[i];
		fprintf(fid, "%d ", eg.m_gID);
		for (int j=0; j<eg.m_eMember.size(); j++) {
			Element& ele = eg.m_eMember[j];
			fprintf(fid, "%d %f ", ele.m_eleID, ele.m_conf);
		}
		fprintf(fid, "\n");
	}
	fclose(fid);
}

void GroupingScheme::printElements(std::string fileName) {
	//
	FILE* fid = fopen(fileName.c_str(), "w");
	for (int i=0; i<m_eleCnt; i++) {
		EleGrp& eg = m_elements[i];
		fprintf(fid, "%d ", eg.m_eID);
		for (int j=0; j<eg.m_gMember.size(); j++) {
			Element& ele = eg.m_gMember[j];
			fprintf(fid, "%d %f ", ele.m_eleID, ele.m_conf);
		}
		fprintf(fid, "\n");
	}
	fclose(fid);
}
mat_3f GroupingScheme::drawAllGrp(int grpCnt) {
	grpEle_vect allGrps = m_groups;
	std::sort(allGrps.begin(),allGrps.end(),grpSizeGreater);
	mat_3f canvas = m_dmPtr->getInput().clone();
	if(grpCnt < 0 || grpCnt > allGrps.size())
		grpCnt = allGrps.size();
	for (int i=0; i<grpCnt; i++) {
		GrpEle& ge = allGrps[i];
		if (ge.m_eMember.size() < 2 ) {
			continue;
		}
		drawGrp(ge, canvas);
	}
	//std::cout<<"# of groups drawn:"<<grpCnt<<std::endl;
	return canvas;
}

void GroupingScheme::saveGrpVis(std::string prefix, std::string gsName,int grpCnt) {
	//sort groups in descend order by their size
	grpEle_vect grps = m_groups;
	std::cout<<"Saving groupings as images, # of groups in total:"<< grps.size()<<std::endl;
	std::sort(grps.begin(), grps.end(), grpSizeGreater);
	char buffer[256];
	grpCnt = (grps.size() > grpCnt ? grpCnt : grps.size());
	int grpToDraw = grpCnt;
	for (int i=0; i< grpToDraw; i++) {
		if (grps[i].m_eMember.size() < 2)
		{
			continue;
		}
		
		mat_3f canvas = m_dmPtr->getInput().clone();
		drawGrp(grps[i], canvas);
		std::string winName(buffer);
		sprintf(buffer, "%s_%s_%06d.png", prefix.c_str(), gsName.c_str(), i);
		std::string sn(buffer);
		cv::imwrite(sn, canvas * 255.0);
	}
	std::string winName(buffer);
	sprintf(buffer, "%s_%s_allGrps_.png", prefix.c_str(), gsName.c_str());
	mat_3f canvas = drawAllGrp(grpCnt);
	std::string sn(buffer);
	cv::imwrite(sn, canvas * 255.0);
}

void GroupingScheme::saveGrpPixelVal(){
	//for each group, display its member's solution
	int grpCnt = m_groups.size() > 10? 10: m_groups.size();
	
	grpEle_vect grps = m_groups;
	
	std::sort(grps.begin(), grps.end(), grpSizeGreater);
	
	for(int i=0;i<grps.size();i++){
		GrpEle& grp = grps[i];
		
	}
}


void GroupingScheme::saveGrpData(std::string prefix, std::string gsName) {
	//

}
void GroupingScheme::group() {

	if (!m_grouped) {
		std::cout<<"Current Grouping Scheme: " << m_gsName << std::endl;
		m_groups.clear();
		m_elements.clear();
		_group(); //grouping pixels 
		_grp2ele(); //group to elements
		_sortNode(); //sort elements	
		//remove group overlap if there is any
		removeGrpOverlap();
		_grp2ele();
		for (int i = 0; i < m_elements.size(); i++)
		{
			EleGrp& eg = m_elements[i];
			if (eg.m_gMember.size() > 1)
			{
				std::cout << "multiple group membership detected" << std::endl;
			}

		}

		_sortNode();
	
		//
		_setMaxGrpIdx(); //for each element, keep its group index with maximum confidence
	}
	m_grouped = true; //group done
}

//void GroupingScheme::setROI(cv::Rect roi) {
//	std::cout << "Setting ROI for current Scheme:" << m_gsName << std::endl;
//	DataManager& dm = *m_dmPtr;
//	cv::Size imgSize = dm.getImgSize();
//	int w = imgSize.width;
//	int h = imgSize.height;
//	std::vector<GrpEle> newGroups;
//	int grpID = 0;
//	for (int i=0; i<m_groups.size(); i++) {
//		GrpEle& ge = m_groups[i];
//		std::vector<Element> newMember;
//		for (int j=0; j<ge.m_eMember.size(); j++) {
//			Element& ele = ge.m_eMember[j];
//			int x = ele.m_eleID % w - roi.x;
//			int y = ele.m_eleID / w - roi.y;
//
//			if (x >= 0 && x < roi.width && y >= 0 && y < roi.height) {
//				Element newEle(x + y * roi.width, ele.m_conf);
//				newMember.push_back(newEle);
//			}
//		}
//		if (!newMember.empty()) {
//			GrpEle nge;
//			nge.m_gID = grpID ++;
//			nge.m_grpType = ge.m_grpType;
//			nge.m_eMember = newMember;
//			newGroups.push_back(nge);
//		}
//	}
//	m_groups = newGroups;
//	m_eleCnt = roi.height * roi.width;
//	_grp2ele();
//	_sortNode();
//	_setMaxGrpIdx();
//}

GroupingScheme::GroupingScheme(DataManager* dmPtr, std::string gsName) :
	m_grouped(false), m_gsName(gsName), m_dmPtr(dmPtr), m_base(1) {

}

void GroupingScheme::eleLink(int cur, std::set<int>& linkedEle) {
	//
	DataManager& dm = *m_dmPtr;
	cv::Size is = dm.getImgSize();
	int curX = cur % is.width;
	int curY = cur / is.width;
	if (curX > 0)//left
		linkedEle.insert(cur-1);
	if (curX < is.width-1)//right
		linkedEle.insert(cur+1);
	if (curY > 0)//above
		linkedEle.insert(cur - is.width);
	if (curY < is.height - 1)//below
		linkedEle.insert(cur + is.width);
}

GroupingScheme::~GroupingScheme() {

}
