#ifndef LAPLACIANOPTIMIZATION_H_
#define LAPLACIANOPTIMIZATION_H_


//#define BIND_FORTRAN_LOWERCASE_UNDERSCORE

#include <boost/numeric/ublas/matrix_sparse.hpp>
#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/io.hpp>
#include "RefGS.h"
#include "ShadingGS.h"

using namespace boost::numeric::ublas;


typedef grpEle_vect Constraint; //
typedef Constraint* ConstraintPtr; //

grpEle_vect loadUserConstraint(mat_3f strokeImg);
 mat_f pinv(mat_f input);
//void verifyUserConstraint(grpEle_vect& strokes,int h , int w);
//void verifyUserConstraint(mat_3f strokeImg, grpEle_vect& strokes, std::vector<cv::Vec3f>& strokeColor);

class Scribble
{
public:
	DataManager* m_dmPtr; 
	ConstraintPtr m_strokePtr; //
	mat_i m_pixScrId; //pixel scribble id
	mat_f m_pixScrConf; //pixel scribble confidence
	Constraint m_scrPix; //pixels of a scribble
	std::vector<cv::Vec3f> m_scrVal; //value for each scribble
	std::vector<float> m_scrWSum; //sum of confidence
protected:
	Scribble(DataManager* dmPtr = NULL, ConstraintPtr strokePtr = NULL)
		:m_dmPtr(dmPtr),m_strokePtr(strokePtr)
	{

	}
public:
	virtual void updateScrVal() = 0;
	virtual cv::Vec3f pixVal(int py,int px) = 0;
public:
	bool isScr(int y, int x){
		return m_pixScrId( y, x) >= 0;
	}
	int scrIdx(int y, int x){
		return m_pixScrId(y,x);
	}
	bool isInited(){
		return m_pixScrId.size().width > 0;
	}

	cv::Vec3f scrVal(int y, int x){
		//float w = m_pixScrConf(y,x);
		float w = 1;
		int idx = scrIdx(y,x);
		return w * m_scrVal[idx];
	}
public:
	virtual void initScribbles(){
		int iw = m_dmPtr->getImgSize().width;
		int ih = m_dmPtr->getImgSize().height;
		m_pixScrId = mat_i(m_dmPtr->getImgSize()); //
		m_pixScrConf = mat_f(m_dmPtr->getImgSize());
		m_pixScrId = -1;
		int scribbleId = 0;
		for (int i = 0; i < m_strokePtr->size(); i++)
		{
			GrpEle  grp = (*m_strokePtr)[i];			
			grp.m_gID = scribbleId;
			m_scrPix.push_back(grp); //save this scribble
			float wSum = 0.0;
			for (int j = 0; j < grp.m_eMember.size(); j++)
			{
				Element& ele = grp.m_eMember[j];
				int px = ele.m_eleID % iw;
				int py = ele.m_eleID / iw;
				m_pixScrConf(py,px) = ele.m_conf; //save the pixel's confidence
				wSum += ele.m_conf;
			}
			m_scrWSum.push_back(wSum);
			
			for (int j = 0; j < grp.m_eMember.size(); j++)
			{
				int ele = grp.m_eMember[j].m_eleID;
				int y = ele / iw;
				int x = ele % iw;
				m_pixScrId(y,x) = scribbleId;
			}
			scribbleId ++; //
		}
		m_scrVal = std::vector<cv::Vec3f>(m_scrPix.size(),cv::Vec3f(0,0,0)); //
	}
	void writeScrPixVal(std::string fileName,bool img = true){
		if (img)
		{
			mat_3f canvas = m_dmPtr->getShading().clone();
			canvas = cv::Vec3f(1,1,1);
			int iw = m_dmPtr->getImgSize().width;
			for (int i = 0; i < m_scrPix.size(); i++)
			{
				GrpEle& ge = m_scrPix[i];
				cv::Vec3f refVal = m_scrVal[i];
				for (int j = 0; j < ge.m_eMember.size(); j++)
				{
					int py = ge.m_eMember[j].m_eleID / iw;
					int px = ge.m_eMember[j].m_eleID % iw;
					cv::Vec3f val = pixVal(py,px);
					//compute vector distance
					cv::Vec3f diffVec = val - refVal;
					diffVec[0] = diffVec[0] < 0? -diffVec[0]: diffVec[0];
					diffVec[1] = diffVec[1] < 0? -diffVec[1]: diffVec[1];
					diffVec[2] = diffVec[2] < 0? -diffVec[2]: diffVec[2];

					canvas(py,px)  = diffVec;
				}
			}
			cv::imwrite(fileName,canvas * 255.0);
		}
		else{
			//
			FILE *fid = fopen(fileName.c_str(),"w");
			if (!fid)
			{
				std::cerr << "failed to open:" << fileName << std::endl;
				return;
			}
			//write the pixel value of each scribble
			int iw = m_dmPtr->getImgSize().width;

			for (int i = 0; i < m_scrPix.size(); i++)
			{
				GrpEle& ge = m_scrPix[i];
				fprintf(fid,"stroke %d: [%f %f %f] ",i,m_scrVal[i][0],m_scrVal[i][1],m_scrVal[i][2]);
				for (int j = 0; j < ge.m_eMember.size(); j++)
				{
					int py = ge.m_eMember[j].m_eleID / iw;
					int px = ge.m_eMember[j].m_eleID % iw;
					cv::Vec3f val = pixVal(py,px);
					fprintf(fid,"[%f %f %f] ",val[0],val[1],val[2]);
				}
				fprintf(fid,"\n\n");
			}
			fclose(fid);
		}
	}

};


struct FixedValue 
{
	float m_val; 
	std::vector<int> m_idxSet;
};


void GaussianSeidel(mat_f& A, mat_f& b, mat_f& x, FixedValue& fv);

void testGS();

class AbsoluteShadeScribble:public Scribble{
public:
	virtual void initScribbles(){
		//
		Scribble::initScribbles();
		//set fixed value
		for (int i = 0; i < m_scrPix.size(); i++)
		{
			GrpEle& ge= m_scrPix[i];
			Element& ele = ge.m_eMember[0];
			m_scrVal[i] = ele.m_rgb;
		}
	}
public:
	AbsoluteShadeScribble(DataManager* dmPtr = NULL, ConstraintPtr strokePtr = NULL)
		:Scribble(dmPtr,strokePtr){}
	virtual cv::Vec3f pixVal(int py,int px) {
		return cv::Vec3f(0,0,0);
	}
	virtual void updateScrVal(){
	}
};

class ConstShadeScribble: public Scribble{
public:
	ConstShadeScribble(DataManager* dmPtr = NULL, ConstraintPtr strokePtr = NULL)
		:Scribble(dmPtr,strokePtr){}
	virtual cv::Vec3f pixVal(int py,int px){
		return m_dmPtr->getShading()(py,px);
	}

	virtual void updateScrVal(){
		//compute the average shading value of each stroke
		mat_3f shadeImg = m_dmPtr->getShading();
		int iw = shadeImg.size().width;
		for (int i = 0; i < m_scrPix.size(); i++)
		{
			GrpEle& grp = m_scrPix[i];
			cv::Vec3f avgS(0,0,0);
			for (int j = 0; j < grp.m_eMember.size(); j++)
			{
				int pixId = grp.m_eMember[j].m_eleID;
				int y = pixId / iw;
				int x = pixId % iw;
				cv::Vec3f tmpS = shadeImg(y,x);
				avgS += tmpS;
			}
			avgS[0] /= grp.m_eMember.size();
			avgS[1] /= grp.m_eMember.size();
			avgS[2] /= grp.m_eMember.size();
			m_scrVal[i] = avgS; //update the scribble shading triple
		}
	}
};

class ConstAlbedoScribble: public Scribble{
public:
	ConstAlbedoScribble(DataManager* dmPtr = NULL, ConstraintPtr strokePtr = NULL)
		:Scribble(dmPtr,strokePtr){}
public:
	virtual cv::Vec3f pixVal(int py,int px){
		cv::Vec3f val = m_dmPtr->getAlbedo()(py,px);
		cv::Vec3f rVal;
		rVal[0] = val[0] > 1e-8 ? 1/val[0]: 0;
		rVal[1] = val[1] > 1e-8 ? 1/val[1]: 0;
		rVal[2] = val[2] > 1e-8 ? 1/val[2]: 0;
		return rVal;
	}
	virtual void updateScrVal(){
		//compute the average albedo value of each stroke
		mat_3f albedoImg = m_dmPtr->getAlbedo();
		mat_3f inputImg = m_dmPtr->getInput();
		mat_3f resultImg = m_dmPtr->getShading(); //shading image
		int iw = albedoImg.size().width;
		for (int i = 0; i < m_scrPix.size(); i++)
		{
			GrpEle& grp = m_scrPix[i];
			cv::Vec3f sumS(0,0,0);
			cv::Vec3f sumI(0,0,0);
			for (int j = 0; j < grp.m_eMember.size(); j++)
			{
				int pixId = grp.m_eMember[j].m_eleID;
				int y = pixId / iw;
				int x = pixId % iw;
				cv::Vec3f tmpS = resultImg(y,x);
				cv::Vec3f tmpI = inputImg(y,x);
				//float conf = m_pixScrConf(y,x)/m_scrWSum[i];
				sumS += tmpS;
				sumI += tmpI;
			}
			//NOTE: the albedo value is inverted
			m_scrVal[i][0] = sumS[0] / sumI[0];
			m_scrVal[i][1] = sumS[1] / sumI[1];
			m_scrVal[i][2] = sumS[2] / sumI[2];
		}
	}
};



#endif
