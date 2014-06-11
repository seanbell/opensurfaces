#ifndef GROUPINGSCHEME_H_
#define GROUPINGSCHEME_H_
#include "cv_header.h"
#include "structDef.h"
#include "DataManager.h"
#include "fw_header.h"
#include <stdio.h>
#include <string>
#include <set>
//#define __OPT_DEBUG__
//#define __LOG_ON__

class GSManager;


bool grpSizeGreater(const GrpEle& ge1,const GrpEle& ge2);

class GroupingScheme
{
	friend class GSManager;
public:
	///common fields
	grpEle_vect m_groups;   //
	eleGrp_vect m_elements;
	int m_eleCnt;
	int m_grpCnt;
	bool m_grouped; //
	std::string m_gsName; //grouping scheme name
	DataManager* m_dmPtr;
	float m_base; //
	///
protected:
	
	void _grp2ele();
	void _sortNode();
	void _setMaxGrpIdx();
	virtual void _group(){};
	
	virtual void _setSoution(int grpID, int eleID, int solution, float& shading){};
	virtual void _grpProperty(int gID,int index, float& shading, float& reflectance){};
	virtual void _eleProperty(int gID, int eleID, int index, float& shading, float& reflectance){};
public:
	GroupingScheme(DataManager* dmPtr =NULL, std::string gsName = "");
	inline grpEle_vect& getGroups(){
		return m_groups;
	}
	void removeGrpOverlap();
	inline eleGrp_vect& getElements(){
		return m_elements;
	}
	virtual void reset(){
		m_groups.clear();
		m_elements.clear();
		m_grouped = false;
	}
	void printGrps(std::string fileName);
	void printElements(std::string fileName);
	virtual void drawGrp(GrpEle& ge, mat_3f& canvas){};
	virtual mat_3f drawAllGrp(int grpCnt = -1);
	virtual void saveGrpVis(std::string prefix,std::string gsName,int grpCnt = 10);
	virtual void saveGrpPixelVal();
	void saveGrpData(std::string prefix,std::string gsName);
	void group();
//	virtual void setROI(cv::Rect roi);
	virtual void eleLink(int cur, std::set<int>& linkedEle);
	virtual ~GroupingScheme();
	
};

#endif /*GROUPINGSCHEME_H_*/
