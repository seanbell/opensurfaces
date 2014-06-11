#include "ShadingGS.h"
#include "AppConfig.h"
ShadingGS::ShadingGS(DataManager* dmPtr,std::string gsName)
:GroupingScheme(dmPtr,gsName)
{
}

ShadingGS::~ShadingGS()
{
	
}

void ShadingGS::_grpProperty(int gID,int index, float& shading, float& reflectance){
	shading = (index+ m_base)/MRF_LABEL_NUM;
}

void ShadingGS::_setSoution(int grpID, int eleID, int solution, float& shading){
	// solution is shading index
	shading = (solution+ m_base) / MRF_LABEL_NUM;
}


void ShadingGS::_eleProperty(int gID, int eleID, int index, float& shading, float& reflectance){

	DataManager& dm = *m_dmPtr;
	mat_3f& inputImg = dm.getInput();
	cv::Size imgSize = inputImg.size();
	int eX = eleID % imgSize.width;
	int eY = eleID / imgSize.width;
	cv::Vec3f& rgb = inputImg(eY,eX);
	float pixInt = cv::norm(rgb);
	shading = (index+ m_base)/MRF_LABEL_NUM;
	reflectance = pixInt / shading;
}


