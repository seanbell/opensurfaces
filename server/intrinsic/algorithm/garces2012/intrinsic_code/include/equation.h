//----------------------------------------------------------------------
//	File:			equation.h
//	Author:			Adolfo Munoz
//	Last modified:	18/07/2012
//	Description:	class which models one equation
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


#ifndef _EQUATION_H_
#define _EQUATION_H_

#include "matrix.h"
#include "math.h"
#include <list>

template <typename real>
class Equation
{
	real weight;
public:

	Equation(real w = 1.0) : weight(w) { }
	void set_weight(real w) { weight = w; }
	virtual real A(int index) const = 0;
	virtual real B() const = 0;

	virtual bool is_valid() const { return (weight != 0.0); }

	void set_row(int row, Matrix<real>& mA, Vector<real>& mB) const
	{
		for (unsigned int c = 0; c<mA.columns();c++) mA(row,c)=weight*this->A(int(c));
		mB(row) = weight*this->B();
	} 
};

template <typename real>
class EquationLogClusterRatio : public Equation<real>
{
	int i,j;
	double b;
	bool valid;
public:
		//We use absolute value in order to avoid negative numbers (in gradients, we just compare absolute values) 
		// and we add a very very small number to avoid zeroes
	EquationLogClusterRatio(int _i, int _j, double value_i, double value_j, double threshold = 0.1 , double weight = 1.0) : Equation<real>(weight),i(_i),j(_j)
	{
		//Threshold assuming 255 maximum. Notice that we are checking that value_i and value_j have the same sign
		valid = ((_i!=_j)&&((value_i*value_j)>(threshold*threshold)));
		if (valid) b=log(fabs(value_j))-log(fabs(value_i));
	}

	real A(int index) const { return (index==i)?1.0:(index==j)?-1.0:0.0; }
	real B() const { return b; }

	bool is_valid() const { return valid; }
};

template <typename real>
class EquationLogCoefficientBalance : public Equation<real>
{
public:
	EquationLogCoefficientBalance(double weight = 1.0) : Equation<real>(weight) { }
	real A(int index) const { return 1.0; }
	real B() const { return 0.0; }
};

template <typename real>
class EquationLogReflectanceEq : public Equation<real>
{
	int i,j;
	double b;
	bool valid;
public:
	
	EquationLogReflectanceEq(int _i, int _j, const double& colorclusteri, const double& colorclusterj, const double& lumclusteri, const double& lumclusterj, double weight = 1.0, double threshold = 0.1) : Equation<real>(weight),i(_i),j(_j) 
	{ 
		double rj = lumclusterj;
		double ri = lumclusteri;
		double rcolorj = colorclusterj;
		double rcolori = colorclusteri;
		//Threshold assuming 255 maximum. Notice that we are checking that ri and rj have the same sign
		valid = ((ri*rj)>(threshold*threshold));		
		if (valid) b=log(fabs(rcolori)) + log(fabs(rj))- log(fabs(rcolorj)) - log(fabs(ri));
	}

	real A(int index) const { return (index==i)?1.0:(index==j)?-1.0:0.0; }
	real B() const { return b; }
};

#endif
