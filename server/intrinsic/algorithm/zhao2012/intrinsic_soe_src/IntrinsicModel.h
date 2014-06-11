#ifndef __INTRINSIC_MODEL__
#define __INTRINSIC_MODEL__

#include "TexturePatchGS.h"
#include "LaplacianOptimization.h"
#include "Matlab.h"
#include "ublas.h"
#include "Utility.h"
#include <opencv/cxcore.h>
#include <opencv/cv.h>
#include <opencv/highgui.h>
#include <vector>
#include "Timer.h"

ublas_cm_f constructShadeSparseMat(Constraint& cons,int w ,int h);
ublas_cm_f constructAlbedoSparseMat(Constraint& cons,int w ,int h);
ublas_cm_f constructRetinexSparseMat(int w ,int h);

class IntrinsicModel{
public:
	mat_u m_ROIMask;
	mat_u m_featureMask; //
public:
	mat_3f m_img; //image at this level
	mat_f m_grayImg; //
	mat_f m_logImg;

	std::string m_modelName;
	DataManager m_dm; //

	ConstShadeScribble m_shadeScrib; //
	ConstAlbedoScribble m_albedoScrib; //
	AbsoluteShadeScribble m_absShadeScrib; //
	bool m_crInited,m_csInited,m_absInited;
	TexturePatchGS m_tpgs;
	Constraint m_cs,m_cr,m_abs; //
	float m_csLambda,m_crLambda,m_absLambda;
	bool m_isCS; //
	bool m_isCR; //
	bool m_isAbsS;//
	bool m_cpnInited; //
	ublas_cm_f m_shadeConsMat; //shade stroke constraint matrix
	ublas_vec_f m_shadeConsVec;
	ublas_cm_f m_albedoConsMat; //albedo stroke constraint matrix;
	ublas_vec_f m_albedoConsVec;
	ublas_cm_f m_absConsMat; //
	ublas_vec_f  m_absConsVec; //absolute shading constraint vector
	ublas_cm_f m_allConsMat; //all constraints
	ublas_vec_f m_allConsVec; //right vector 
	ublas_vec_f m_solutionVec; //solution
	bool m_eqCons; //whether use equality constraint
	ublas::matrix<mat_f> m_mpinvMat; //pseudoinverse of "m" matrix
	ublas::matrix<mat_f> m_aVecMat; //"a" vector of each pixel
	double m_solveTime; //
	double m_matrixTime;
	double m_sparsity;
public:
	//these variables are declared for Laplacian matrix formulation
	ublas_mat_f m_lapMat;
	ublas_cm_f m_sLapmat; //sparse laplacian matrix
	int m_lWinSize;
	bool m_matBuild; //
public:
	mat_3f m_pixNorm; //pixel's shading normal	
	//

public:
	IntrinsicModel(mat_3f img, std::string modelName = "BASE");
	void setLocalWindowSize(int sz){
		m_lWinSize = sz; //set the local window size
	}
	void setPixNorm(mat_3f pixNorm){
		m_pixNorm = pixNorm.clone();
	}
	void lMat2sLmat();
	void setROIMask(mat_3f maskImg = mat_3f(0,0));
	void setFeatureMask(mat_3f maskImg = mat_3f(0,0));
	void addShadeScrib(Constraint& cons,float w = 1.0);
	void addAlbedoScrib(Constraint& cons,float w = 1.0);
	void addAbsShadeScrib(Constraint& cons, float w = 1.0);
	Constraint genConsAlbedoCons(float distThrd = 0.001, float varThrd = 0.1); //generate constant albedo constraints
	Constraint genConsShadeCons();
	Constraint genAbsShadeCons(float val = 1.0);
	//void visConstraint();
	void reduceSdEdge();
	void decompose(bool normSd = false,bool normRef = false,bool wse  = false, bool gamma = false);
	static void gammaCorrect(mat_3f img, float gamma);
	void saveAlbedoConsVis(std::string basePath, std::string imgName);
	void saveResult(std::string basePath, std::string imgName);
	void solve();
	void saveConsGrpVal(std::string basePath,std::string imgName);
	void saveSparseMatrix(std::string rootPath = "d:\\ELEZQI");
	virtual ~IntrinsicModel();
public:
	void init();
	void initCPNlMatrix(int lWinSize); //
	void computeAVec();
	mat_3f aVec2Mat3f();
	void visAVec();
	void avgCPNormal(bool distWeithed = true);
	mat_3f decomposeFromAVec();

	Constraint maskConstraint(Constraint& cons);
	static Constraint dszCons(int sz11, int sz12, Constraint cons);
	static Constraint uszCons(int sz11, int sz12, int sz21, int sz22, Constraint cons);
	ublas::matrix<mat_f> uszAVec(int sz21, int sz22);

public:
	DataManager& getDM(){
		return m_dm;
	}
protected:
	virtual void _solve()  = 0; //by matlab default
	virtual void _cons2SparseMat();
	void _buildLaplacianMatrix();
	virtual void _init() = 0; //class specific initialization
	virtual void _shadeConstraint2SparseMat();
	virtual void _albedoConstraint2SparseMat();
	virtual void _absoluteShadeConstraint2SparseMat();
};


class IMConfig{
public:
	static float shadeLambda;
	static float albedoLambda;
	static float absLambda;
	static float windowSize;
	static bool  useEqCons; //
	static float chromThrd;
	static float txVar; // texture variance
	static float distThrd; //distance threshold
	static float rWeight; //reflectance component weight
};

#endif
