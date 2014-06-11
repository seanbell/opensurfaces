#if 0
#ifndef __PMVS_PATCH_H__
#define __PMVS_PATCH_H__
#include "cv_header.h"
#include "structDef.h"
#include "NormalEstimator.h"
#include "PixelNormGS.h"
#include <vector>
#include <set>
//#include "Delaunay.h"

//#define __DUMP_FILE__

class Patch
{
public:
	cv::Vec3f m_pt;
	cv::Vec3f m_norm;
	uchar m_r;
	uchar m_g;
	uchar m_b;
	float m_photoConsistency; //
	float m_debug1;
	float m_debug2;
	int m_visCnt1;
	std::vector<int> m_visIndex1;
	int m_visCnt2;
	std::vector<int> m_visIndex2;
	std::set<int> m_visIndex;
	std::vector<bool> m_visFlag; //
	bool m_normAvaiable; //
public:
	Patch();
	void idx2bool();
	mat_3f visNorm();
	virtual ~Patch();
};



class ViewInfo{
public:
	int m_viewIdx;
	std::string m_viewImgFile;
	//view image
	mat_3f m_viewImg;
	///project matrix
	mat_f m_prjMat;
	///pixel normal
	mat_3f m_pixNorm;
	///pixel normal mask
	mat_u m_normMask;
	///roi mask
	mat_u m_roiMask;
	//
	cv::Vec3f m_centerPos; //camera center position
	bool m_ccEstiamted; //
protected:
	void _estiamteCameraCenter();
public:
	static mat_f eqMatFromImgPt(mat_f& prjMat, cv::Vec2f& p);
	static cv::Vec3f convergePoint(mat_f& prjMat, std::vector<cv::Vec2f>& ptSeq);
public:
	ViewInfo();
	void createStruct(mat_3f img = mat_3f(0,0), int viewIdx = -1,std::string viewImgFile = "");
	inline void setMask(mat_u msk){
		m_roiMask = msk.clone();
	}
	void interplation();
	void applyMask();
	void projectPatch(std::vector<Patch>& patchList);
	mat_3f visNorm();
	void save();
	virtual ~ViewInfo();
};

class PMVS2{

protected:
	std::string m_pmvsRootPath;
	std::string m_txtPath;
	std::string m_visPath;
	std::string m_modelPath;
	std::string m_patchFile;
	std::string m_plyFile;
	std::string m_ptFile;
	std::vector<std::string> m_txtFile;
	int m_viewCnt;
	std::vector<Patch> m_patchList;
	std::vector<ViewInfo> m_viewInfo;
	//////////////////////////////////////////////////////////////////////////
	std::vector<mat_f> m_camParaList;
protected:
	void _init();
	void _getViewCnt();
	void _loadCamMatrix();
	void _loadPatch();
	void _loadPly();
	void _saveEstimatedNormalAsPly();
	void _loadModel();
	void _estimateNormal();
public:
	PMVS2(std::string pmvsRootPath);
	ViewInfo& getViewInfo(int viewIdx);
	void loadViewInfo(int idx = -1);
	void deleteViewInfo(int idx = -1);
	//void doProjection();
	virtual ~PMVS2();
};



#endif
#endif
