/*
 * DataManager.h
 *
 *  Created on: 2010-1-6
 *      Author: zhaoqi
 */

#ifndef DATAMANAGER_H_
#define DATAMANAGER_H_
#include "structDef.h"
#include "Pixel.h"
#include "PixelGroup.h"
#include <opencv/cxcore.h>


void interpValue(mat_3f mat, mat_u &mask, int py,int px, int winSz);

/*!
 *\brief manage all the images
 *
 *
 */
class DataManager {
protected:
	///input rgb image
	mat_3f m_inputImg;
	/// chromacity image, shading free
	mat_3f m_chromImg;
	/// shading component
	mat_3f m_shadingImg;
	/// reflectance component
	mat_3f m_albedoImg;
	mat_f m_shadeErr; //shade error
	mat_f m_refErr; //reflectance err
	mat_f m_intErr; //intensity error
	mat_u m_srMask; //pixels belongs to shading and reflectance will be set to 255
	mat_u m_mask;
	cv::Size m_imgSize;
	vect_pg m_pgVec; //
	vec_pixel m_pixVec; //pixel vector
	mat_3f m_pixNorm; //pixel norm
//protected:
//	static DataManager m_globalDM;
public:
	DataManager();
	static void normalizeImage2(mat_3f& mat,mat_u& mask);
	static void normalizeImage(mat_3f& mat,mat_u& mask);
	static void rgb2chrom(mat_3f& mat);
//	static DataManager& getDM(){
//		return m_globalDM;
//	}
public:
	void init(mat_3f& inputImg,mat_u* maskPtr=NULL);
	vect_pg& getPgVec(){
		return m_pgVec;
	}
	void normImage();
	void saveResult(std::string basePath, std::string baseName);
	void savePixelGroup(std::string& fileName);
	void loadPixelGroup(std::string& fileName);
	static void erodeBinaryImage(mat_f img);
	mat_3f& getInput(){
		return m_inputImg;
	}
	mat_3f& getChrom(){
		return m_chromImg;
	}
	mat_3f& getShading(){
		return m_shadingImg;
	}
	mat_3f& getAlbedo(){
		return m_albedoImg;
	}
	mat_f& getShadeErrImg(){
		return m_shadeErr;
	}
	mat_f& getRefErrImg(){
		return m_refErr;
	}
	mat_f& getIntErrImg(){
		return m_intErr;
	}
	cv::Size& getImgSize(){
		return m_imgSize;
	}
	vec_pixel& getPixelVec(){
		return m_pixVec;
	}
	mat_u& getMask(){
		return m_mask;
	}
	mat_u& getSRMask(){
		return m_srMask;
	}
	virtual ~DataManager();
};

#endif /* DATAMANAGER_H_ */
