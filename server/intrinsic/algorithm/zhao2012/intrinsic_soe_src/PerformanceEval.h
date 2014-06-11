#ifndef __PERFORNANCE_EVAL__
#define __PERFORNANCE_EVAL__

#include "IntrinsicModel.h"
#include "RetinexIntrinsic.h"


class PerformanceEvaluator{
public:
	bool m_mitData;
	std::string m_inputRootPath; //
	std::string m_resultRootPath; //
	std::vector<std::string> m_objectPaths; //
public:
	PerformanceEvaluator(std::string configFilePath)
		:m_mitData(false){
		m_objectPaths = loadExpConfig(configFilePath);
	}
	void evaluate(std::string methodName = "RI");
public:
	void eval();
	void testThrd();
	void mitEval();
	std::vector<std::string> loadExpConfig(std::string imgListPath);
	static mat_f rgb2gray(mat_3f img);
	static mat_f mask2float(mat_u msk);
	static float MSE(mat_f vec1,mat_f vec2, mat_f fMsk);
	static float LMSE(mat_3f estImg, mat_3f gtImg, mat_3f fMsk, int winSize);
	static float scoreImg(mat_3f estSd,mat_3f estRef, mat_3f gtSd, mat_3f gtRef, mat_3f msk);
};


#endif