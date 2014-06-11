//----------------------------------------------------------------------
//	File:			preconditioners.h
//	Author:			Adolfo Munoz
//	Last modified:	18/07/2012
//	Description:	preconditioners
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

#ifndef _PRECONDITIONERS_H_
#define _PRECONDITIONERS_H_

template<typename real>
class PreconditionerSqrootDiagonal
{
   Vector<real> f; 
   public:
       PreconditionerSqrootDiagonal(const Matrix<real>& m) : f(m.columns())
       {
		for (unsigned int i=0;(i<m.columns())&&(i<m.rows());i++)
			f(i)=1.0/sqrt(m(i,i));
       }

       Vector<real> solve(const Vector<real>& v) const
       {
		Vector<real> s(f.size());
	   for (unsigned int i=0;i<f.size();i++) s(i)=v(i)*f(i);
	   return s;
       }

       Vector<real> trans_solve(const Vector<real>& v) const { return solve(v); }
};

template<typename real>
class PreconditionerIdentity
{
   public:
       const Vector<real>& solve(const Vector<real>& v) const { return v; }
       const Vector<real>& trans_solve(const Vector<real>& v) const { return v; }
};


#endif
