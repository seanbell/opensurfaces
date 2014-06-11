#ifndef ANNCLUSTER_H_
#define ANNCLUSTER_H_

#include "structDef.h"
#include "fw_header.h"
#ifdef __USE_ANN__
#include <ANN/ANN.h>
#else
#include "cv_header.h"
#endif
class ANNCluster
{
public:
	ANNCluster();
	void doCluster(mat_f& data, grpEle_vect& grpVect, float radius);
	virtual ~ANNCluster();
};

#endif /*ANNCLUSTER_H_*/
