/*
 * PixelGroup.h
 *
 *  Created on: 2010-1-6
 *      Author: zhaoqi
 */

#ifndef PIXELGROUP_H_
#define PIXELGROUP_H_
#include "structDef.h"
#include <vector>
#include "cv_header.h"
/*!
 *\brief hold pixels which are likely to have identical reflectance in a group
 *
 *
 */
struct PixelGroup {
	///reflectance index
	int m_refIndex;
	///pixels in this group
	vect_i m_pixelID;
	///pixel confidence, weighting the energy term
	vect_f m_conf;
	///average chromacity vector
	cv::Vec3f m_chrom;
	//average rgb
	cv::Vec3f m_rgb; 
	///the maximum intensity of the pixels in this group(input image), used for normalization
	float m_maxIntensity;
	PixelGroup()
	:m_refIndex(-1)
	,m_chrom(0,0,0)
	,m_rgb(0,0,0){

	}
	void readFromFile(FILE* fid);
	void writeToFile(FILE* fid);
};

typedef std::vector<PixelGroup> vect_pg;

#endif /* PIXELGROUP_H_ */
