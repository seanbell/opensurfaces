#ifndef TEXTUREPATCHGS_H_
#define TEXTUREPATCHGS_H_
#include "RefGS.h"
#include "structDef.h"
#include "fw_header.h"

#include <ANN/ANN.h>

#define  __MODIFY__
//#define  __REFINE_GRP__
#define __AVG_PATCH__

#define PATCHSCALENUM 3
#define Label_Num 50

/*
 * some structures from Shen Li's Implementation
 */

typedef std::vector <int> vect_i;
typedef std::vector <float> vect_f;
typedef std::vector <vect_i> vect;

typedef struct {
	bool m_istextured;
	vect_i m_chainId;
	vect_f m_confidence;
} TxPixel;

typedef struct {
	float m_chrom[3];
	int m_shading; // m_reflectance;
	vect_i m_pixelID;
	vect_i m_windowsize;
	vect_f m_confidence;
	vect_i m_rotation;
	float m_Imax;
} SuperPixel;

typedef std::vector <SuperPixel> vec;

class TexturePatchGS : public RefGS {
public:
	std::vector<TxPixel> m_txPixels;
	vec m_txChains;
	vect_i m_txPixelId;
	int m_iWidth;
	int m_iHeight;
	float m_trd_noise;
	int m_patchsize;
	float m_trd_dist;
	float m_trd_max; //pixel maximum distance
	float m_trd_chrvar;
	char m_rotation;
	bool m_IsMultipleMatch;
	bool m_IsSoftMatch;
	int m_iternum;
	float m_smoothS;
	float m_smoothR;
	FILE* m_logFID;
public:
	TexturePatchGS(DataManager* dmPtr = NULL, std::string gsName="TPGS");
	void getPatch(mat_3f& input, int l, int t, int patchSize, int rotation,
			float* data);
	float computeVar(mat_f& A);
	void buildTxPool();
	void Rotation(ANNpoint queryPt, ANNpoint dataPt, int r, int patchsize);
	void RotationAdd(ANNpoint queryPt, ANNpoint dataPt, int r, int patchsize);
	void Cluster(vect_i& pixelId, int patchsize);
	void DestryKdTree(ANNkd_tree * tree);
	void TextureMatch(ANNpointArray dataPts, int patchsize, vect_i& pixelId,
			vec& groups);
	void TextureMatch2(ANNpointArray dataPts, int patchsize, vect_i& pixelId,
		vec& groups);
	mat_3f CreateMozacCanvas(int hMaxCnt, int vMaxCnt, int patchSize, int sep);
	void MozacPatch(mat_3f& canvas, mat_3f& patch, int patSep, int patchId);

	void FetchPatch(mat_3f& input,int y ,int x, mat_3f& patch){
		int pSize=  patch.size().width;
		for (int i = 0; i <  pSize; i++)
		{
			for (int j = 0; j < pSize;j ++)
			{
				patch(i,j) = input(y + i, x + j);
			}
			
		}
		
	}
	static void PatchRotation(mat_3f& input, mat_3f& rotMat,int r);
	void RefineGrp(SuperPixel& sp);
	void GrpMozac(std::string basePath);
	void VisAllGrp(std::string basePath, int chainID = -1); //visualization all groups in one image
	void Texturematch(void);
	void SetTxPixels();
	void chains2groups();
	void CheckLargerWindow(int windowsize);
	float updateGrpConf(int grpID, int pixID);
	void printTxChains(std::string fileName);
	void printTxPixels(std::string fileName);
	int IsIn(int p, vect_i & v);
	void DecomposeImg();
	void Twroptimize();
	virtual ~TexturePatchGS();
protected:
	virtual void _group();
};


#endif /*TEXTUREPATCHGS_H_*/
