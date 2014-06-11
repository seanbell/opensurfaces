//----------------------------------------------------------------------
//	File:			matte.h
//	Author:			Adolfo Munoz
//	Last modified:	18/07/2012
//	Description:	class to control the mask file
//----------------------------------------------------------------------
// This file is part of Intrinsic Images by Clustering.
//
//    Intrinsic Images by Clustering is free software: you can redistribute it 
//    and/or modify it under the terms of the GNU General Public License as 
//    published by the Free Software Foundation, either version 3 of the License,
//     or (at your option) any later version.
//
//    Intrinsic Images by Clustering is distributed in the hope that it will
//    be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//    GNU General Public License for more details.
//
//    You should have received a copy of the GNU General Public License
//    along with Intrinsic Images by Clustering.  If not, 
//	  see <http://www.gnu.org/licenses/>.
////----------------------------------------------------------------------

#ifndef _IMAGING_MATTE_H
#define _IMAGING_MATTE_H

#include "CImg.h"
using namespace cimg_library;

namespace Imaging
{

class Matte
{
public:	
	
	virtual bool operator()(int x, int y) const = 0;
	
};

class MatteAll : public Matte 
{
public:
	bool operator()(int x, int y) const { return true; }
};

class MatteNone : public Matte
{
public:
	bool operator()(int x, int y) const { return false; }
};

class MatteImage : public Matte
{
	CImg<float> image;
public:
	
	
	MatteImage(){}
	MatteImage(const char* filename) : image(filename) { }	
	MatteImage(const CImg<float>& i) : image(i) { }
	
	void set(int x, int y, bool v) { image(x,y,0,0) = (v?255.:0.); }
	bool operator()(int x, int y) const { return (image(x,y,0,0)>250.); }
	
};

};


#endif
