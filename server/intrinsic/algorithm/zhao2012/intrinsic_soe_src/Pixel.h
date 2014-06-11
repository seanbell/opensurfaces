/*
 * Pixel.h
 *
 *  Created on: 2010-1-7
 *      Author: zhaoqi
 */

#ifndef PIXEL_H_
#define PIXEL_H_
#include "structDef.h"

struct Pixel {
	vect_i m_groupID;
	///confidence in this field
	vect_f m_groupConf;
	///
};
typedef std::vector<Pixel> vec_pixel;
#endif /* PIXEL_H_ */
