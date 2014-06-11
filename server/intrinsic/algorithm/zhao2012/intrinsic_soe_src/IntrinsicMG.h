#if 0
#ifndef INTRINSICMG_H
#define INTRINSICMG_H

#define BIND_FORTRAN_LOWERCASE_UNDERSCORE
#include "LaplacianOptimization.h"
#include "Matlab.h"
#include <engine.h>
#include "ublas.h"
#include <opencv/cxcore.h>
#include <opencv/cv.h>
#include <opencv/highgui.h>
#include <vector>
#include "IntrinsicModel.h"
#include "RetinexIntrinsic.h"
#include "LaplacianIntrinsic.h"

/*
Customized MultiGrid algorithm for intrinsic image decomposition. 
The major difference from standard MG is that it does not use sparse
matrix. The performance should be higher
*/

class IntrinsicLevel;
typedef IntrinsicLevel* IntrinsicLevelPtr;

class IntrinsicLevel
{
protected:
	bool m_isCS; //
	bool m_isCR; //
	bool m_isAbsS;//
	int m_level; //level at the pyramid
public:
	DataManager m_dm; //
	mat_3f m_img; //image at this level
	mat_3f m_shadeStrokeImg; //
	mat_3f m_albedoStrokeImg; //
	mat_3f m_absShadeImg; //absolute 
	int m_lWinSize; //local window size
	Constraint m_consShade; //constant shade
	Constraint m_consRef; //constant reflectance
	Constraint m_absShade; //absolute shading

	ConstShadeScribble m_shadeScrib; //
	ConstAlbedoScribble m_albedoScrib; //
	AbsoluteShadeScribble m_absShadeScrib; //

	ublas_mat_f m_lapMat; //laplacian matrix at current level
	ublas::matrix<mat_f> m_mpinvMat; //pseudoinverse of "m" matrix
	ublas::matrix<mat_f> m_aVecMat; //"a" vector of each pixel
	bool m_matBuild; //
public:
	ublas_cm_f m_sLapmat; //sparse laplacian matrix
	ublas_cm_f m_shadeConsMat; //shade stroke constraint matrix
	ublas_cm_f m_albedoConsMat; //albedo stroke constraint matrix;
	ublas_cm_f m_shadeSmthMat; //shade smoothness constraint
	ublas_cm_f m_albedoStrokeMat; //
	ublas_cm_f m_absDiagMat; //
	ublas_vec_f  m_absConsVec; //absolute shading constraint vector
	ublas_cm_f m_allConsMat; //all constraints
protected:
	IntrinsicLevel(const IntrinsicLevel& il);
	 void setStrokePix(mat_3f& strokeImg, Constraint& cons);
	IntrinsicLevel& operator=(const IntrinsicLevel& il);
public:
	IntrinsicLevel(mat_3f img, int level = 0, int lWinSize = 3,ConstraintPtr consShadePtr = NULL,
		ConstraintPtr constRefPtr = NULL,
		ConstraintPtr absShadePtr = NULL);
	IntrinsicLevelPtr downSample();
	IntrinsicLevelPtr upSample(int sz1, int sz2); //
	Constraint dszCons(int sz11, int sz12, Constraint cons);
	Constraint uszCons(int sz11, int sz12, int sz21, int sz22, Constraint cons);
	ublas::matrix<mat_f> uszAVec(int sz21, int sz22);
	void testGSOptimize();
	ublas_vec_f GSOptimize( ublas_vec_f& u0,int iterCnt, float m_lambdaConstrain,float epsilon);
	void decompose();
	void smoothShading();
	//void visConstraint();
	void buildLMat(); //build laplacian matrix
	void computeAVec();
	void visAVec();
	void constraint2SparseMat(bool css = false, bool cas = false, bool sm = false);
	void shadeConstraint2SparseMat();
	void albedoConstraint2SparseMat();
	void shadeSmoothConstraint2SparseMat();
	void absoluteShadeConstraint2SparseMat();
	void lMat2sLmat();
	void saveImages(std::string basePath,std::string imgName);
	ublas_vec_f matlabSolve();
	void saveSparseMat(std::string basePath);
	mat_3f computeShadingFromAVec();
public:
	static std::vector<mat_f> splitClrImg(mat_3f input);
	static mat_3f mergeClrImg(std::vector<mat_f>& input);
	static mat_f dszImg(mat_f origImg);
	static mat_f uszImg(mat_f origImg, int sz1, int sz2);
	static ublas_vec_f cvMat2UblasVec(mat_f mat);
public:
	~IntrinsicLevel(){}
};


typedef IntrinsicModel* IMPtr; 
class PyramidIntrinsic:public IntrinsicModel
{
protected:
	std::string m_levelModelName;
public:
	int m_levelCnt; //number of levels
	bool m_genCons; //
	std::vector<IMPtr> m_levels; //
	mat_3f m_botSdImg; //
	mat_3f m_botRefImg;
public:
	PyramidIntrinsic(mat_3f origImg, int lWinSize = 3, int levelCnt = 3, ConstraintPtr conShadePtr = NULL,
		ConstraintPtr consRefPtr = NULL, ConstraintPtr absShadePtr = NULL,std::string modelName = "RI",bool genCons = true);

	void verifyPry();
	void solveByUszAVec(bool useMatlab = true);
	void saveResult(std::string pathBase, std::string igmName);
	void releasePyramid();
	~PyramidIntrinsic();
protected:
	virtual void _init();
	virtual void _solve();
	virtual void _cons2SparseMat(){};
	PyramidIntrinsic(const PyramidIntrinsic& il);
	PyramidIntrinsic& operator= (const PyramidIntrinsic& il);
};


IntrinsicModel* downsampleIM(IntrinsicModel* imPtr);




#endif
#endif
