#ifndef PIXELNORMGS_H_
#define PIXELNORMGS_H_
#include "ShadingGS.h"
#include "cv_header.h"

#define __ANN_GRP__

class PixelNormGS: public ShadingGS
{
public:
	mat_3f m_3dNormImg;
	mat_u  m_mask;
public:
	PixelNormGS(DataManager* dmPtr = NULL, mat_3f normImg=mat_3f(), mat_u mask=mat_u());
	mat_3f drawMask();
	void GrpMozac(std::string basePath);
	virtual void drawGrp(GrpEle& ge,mat_3f& canvas);
	virtual ~PixelNormGS();
protected:
	virtual void _group();
	void _interpolation();
	
};

#endif /*PIXELNORMGS_H_*/
