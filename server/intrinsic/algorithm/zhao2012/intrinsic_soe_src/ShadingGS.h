#ifndef SHADINGGS_H_
#define SHADINGGS_H_
#include "GroupingScheme.h"

//grouping pixels based on shading

class ShadingGS : public GroupingScheme
{
	
public:
	ShadingGS(DataManager* dmPtr = NULL,std::string gsName = "");
	virtual ~ShadingGS();
protected:
	virtual void _grpProperty(int gID,int index, float& shading, float& reflectance);
	virtual void _setSoution(int grpID, int eleID, int solution, float& shading);
	virtual void _eleProperty(int gID, int eleID, int index, float& shading, float& reflectance);
};

#endif /*SHADINGGS_H_*/
