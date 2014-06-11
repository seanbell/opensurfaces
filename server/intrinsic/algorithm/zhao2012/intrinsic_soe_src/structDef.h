/*
 * structDef.h
 *
 *  Created on: 2010-1-6
 *      Author: zhaoqi
 */

#ifndef STRUCTDEF_H_
#define STRUCTDEF_H_
#include <vector>
#include <opencv/cxcore.h>
#include <iostream>

#define math_max(a,b) (a)>(b)?(a):(b)
typedef std::vector<int> vect_i;
typedef std::vector<float> vect_f;
typedef cv::Mat_<int> mat_i;
typedef cv::Mat_<cv::Vec3f> mat_3f;
typedef cv::Mat_<float> mat_f;
typedef cv::Mat_<uchar> mat_u;

#endif /* STRUCTDEF_H_ */
