#ifndef REFGS_H_
#define REFGS_H_
#include "GroupingScheme.h"
#include "AppConfig.h"

//grouping based on reflectance

class RefGS : public GroupingScheme {
	friend class GSManager;
public:
	std::vector<float> m_grpMaxIntensity;
	std::vector<cv::Vec3f> m_grpChromVect;
public:
	RefGS(DataManager* dmPtr = NULL,std::string gsName = "");
//	virtual void saveGrpVis(std::string prefix,std::string gsName);
	virtual ~RefGS();
protected:
	void getGrpMaxInt();
	void getGrpChrom();
	virtual void drawGrp(GrpEle& ge, mat_3f& canvas);
	virtual void _grpProperty(int gID,int index, float& shading, float& reflectance);
	virtual void _setSoution(int grpID, int eleID, int solution, float& shading);
	virtual void _eleProperty(int gID, int eleID, int index, float& shading,
			float& reflectance);

};

#endif /*REFGS_H_*/
