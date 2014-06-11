//----------------------------------------------------------------------
//	File:			equation-system.h
//	Author:			Adolfo Munoz
//	Last modified:	18/07/2012
//	Description:	class which models the system of equations
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

#ifndef _EQUATION_SYSTEM_H_
#define _EQUATION_SYSTEM_H_



#include "matrix.h"
#include "math.h"
#include "equation.h"
#include <list>

namespace ublas = boost::numeric::ublas;


template <typename real>
class EquationSystemOnTheFly
{
	Matrix<real> _A; Vector<real> _B;
public:
	template<typename E>
	bool add_equation(const E& e)
	{
		if (e.is_valid()) 
		{
			for (unsigned int i = 0; i<_A.columns();i++)
			{
				double a = e.A(i);
				if (a!=0)
				{
					for (unsigned int j = 0; j<_A.columns();j++)
						_A(i,j)+=a*e.A(j);
				}
			}

			double b = e.B();
			if (b!=0)
			{
				for (unsigned int j = 0; j<_A.columns();j++)
					_B(j)+=b*e.A(j);
			}
			return true;
		}
		return false;
	}

	void add_equation_pointer(const Equation<real>* eq)
	{
		if (eq) { add_equation(*eq); delete eq; }
	}
	

	void clear()
	{		
		for (unsigned int i = 0; i<_A.columns(); i++)
		{
			_B(i) = 0.0;
			for (unsigned int j = 0;j<_A.columns(); j++)
				_A(i,j) = 0.0;
		}
	}

	EquationSystemOnTheFly(int c) : _A(c,c),_B(c) { this->clear(); }
	~EquationSystemOnTheFly() { this->clear(); }

	void build_matrices(Matrix<real>& A, Vector<real>& B) const
	{
		A = _A; B = _B;
	}
};

#endif
