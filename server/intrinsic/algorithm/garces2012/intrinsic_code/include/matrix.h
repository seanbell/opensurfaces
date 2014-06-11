//----------------------------------------------------------------------
//	File:			matrix.h
//	Author:			Adolfo Munoz
//	Last modified:	18/07/2012
//	Description:	operations with matrices
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

#ifndef _MATRIX_H_
#define _MATRIX_H_

//template <typename real = float >
//class Vector;

template <typename real = float>
class Matrix
{
public:
	typedef real* Row;
private:

	unsigned int nrows;	//rows
	unsigned int ncols;	//columns
	unsigned int nelms;	//elements

	real*   data;	// Matrix store
	Row*     a;		// access to element[nrows][ncols]

	void alloc(unsigned int r,unsigned int c)
	{
		nrows = r;
		ncols = c;
		nelms = nrows * ncols;
		data  = new real[nelms];
		a     = new Row  [nrows];
		#pragma parallel		
		for (unsigned int i = 0; i < nrows; i++)
			a[i] = data + i * ncols;
	}

	void clean()
	{
		nrows = 0;
		ncols = 0;
		nelms = 0;
		if (a)    delete[] a;
		if (data) delete[] data;
	};

public:

	Matrix() : nrows(0), ncols(0), data(0), a(0)
	{
	};
	Matrix(unsigned int s)
	{
		alloc(s, s);
	};
	Matrix(unsigned int r,unsigned int c)
	{
		alloc(r, c);
	};
	Matrix(real* k, unsigned int r, unsigned int c)
	{
		alloc(r, c);
		for (unsigned int i = 0; i < elements(); i++)
			data[i] = k[i];
	};
	Matrix(const Matrix& that) : nrows(0), ncols(0), data(0), a(0)
	{
		copy(that);
	};
	~Matrix()
	{
		clean();
	};

	void resize(unsigned int r,unsigned int c)
	{
		clean();
		alloc(r, c);
	};
	void copy(const Matrix& that)
	{
		if (this != &that)
		{
			resize(that.rows(), that.columns());
			for (unsigned int i = 0; i < elements(); i++)
				data[i] = that.data[i];
		}
	};

	const Matrix& operator=(const Matrix& that);

	unsigned int	rows    () const { return nrows; };
	unsigned int	columns () const { return ncols; };
	unsigned int	elements() const { return nelms; };

	const  Row&     operator [] (unsigned int r)        const { return a[r];    };
	const  real&   operator () (unsigned int r, int c) const { return a[r][c]; };
		   real&   operator () (unsigned int r, int c)       { return a[r][c]; };

	Matrix	operator +  ()                    const;
	Matrix	operator -  ()                    const;
	Matrix	operator +  (const Matrix& that)  const;
	Matrix	operator -  (const Matrix& that)  const;
	Matrix	operator *  (const Matrix& that)  const;
	Matrix	operator *  (real k)              const;

	template<class real2>
	friend Matrix<real2>	operator *(real2 k, const Matrix<real2>& A);

	// Kronecker, Direct sum
	template<class real2>
	friend Matrix<real2>  kroneckerSum(const Matrix<real2>& A, const Matrix<real2>& B);

	// Hadamard, Schur or Elementwise product
	template<class real2>
	friend Matrix<real2>  hadamardProduct (const Matrix<real2>& A, const Matrix<real2>& B);

	// Kronecker, Direct or Tensor product
	template<class real2>
	friend Matrix<real2>  kroneckerProduct(const Matrix<real2>& A, const Matrix<real2>& B);

	template<class real2>
	friend Matrix<real2>  commutator      (const Matrix<real2>& A, const Matrix<real2>& B);

    	// Transpose and multiply
	Matrix   trans_mult  (const Matrix& that) const;

	const  Matrix&	operator += (const Matrix& that);
	const  Matrix&	operator -= (const Matrix& that);
	const  Matrix&	operator *= (const Matrix& that);
	const  Matrix&	operator *= (real k);

	// Matrices relations
	template<class real2>
	friend bool     homogeneus(const Matrix<real2>& A, const Matrix<real2>& B);

	template<class real2>
	friend bool     equivalent(const Matrix<real2>& A, const Matrix<real2>& B); // iff they have the same rank

	template<class real2>
	friend bool     equal     (const Matrix<real2>& A, const Matrix<real2>& B);

	template<class real2>
	friend bool     equalSize (const Matrix<real2>& A, const Matrix<real2>& B);
	
	template<class real2>
	friend bool     compatible(const Matrix<real2>& A, const Matrix<real2>& B);
		   bool		operator == (const Matrix& that) const { return equal((*this), that); };


	//Elementary Row and Column Operations
	void swapRows        (const int& r1, const int& r2);
	void swapColumns     (const int& c1, const int& c2);
	void addRowTo        (const int& r1, const int& r2, const real& k = 1.0e0);
	void addColumnTo     (const int& c1, const int& c2, const real& k = 1.0e0);
	void multiplyRowBy   (const int& r,  const real& k);
	void multiplyColumnBy(const int& c,  const real& k);

	// BlockMatrix and Submatrix Creation
	       Matrix rowVector       (const int& r) const;
	       Matrix columnVector    (const int& c) const;
	       Matrix eliminateRow    (const int& r) const;
	       Matrix eliminateColumn (const int& c) const;
	       Matrix eliminateElement(const int& r, const int& c) const;
	       Matrix submatrix       (const int& r1, const int& c1, const int& r2, const int& c2) const;
	template<class real2>
	friend Matrix concatenate(const Matrix<real2>& AL, const Matrix<real2>& AR);
	template<class real2>
	friend Matrix stack      (const Matrix<real2>& AT, const Matrix<real2>& AB);


	// Properties
	Matrix mainDiagonal   (const int& d) const;
	Matrix antiDiagonal   (const int& d) const;
	Matrix mainDiagonal   ()             const { return mainDiagonal(0);  };
	Matrix antiDiagonal   ()             const { return antiDiagonal(0);  };
	Matrix subDiagonal    ()             const { return mainDiagonal(1);  };
	Matrix superDiagonal  ()             const { return mainDiagonal(-1); };
	int    upperBandwidth ()             const;
	int    lowerBandwidth ()             const;
	int    bandwidth      ()             const { return max(lowerBandwidth(), upperBandwidth()); };
	real  conditionNumber()             const;

	int    rank            ()             const;

	template<class real2>
	friend bool RothsRemovalRule(const Matrix<real2>& A, const Matrix<real2>& X, const Matrix<real2>& B, const Matrix<real2>& C);

	real cofactor(const int& r, const int& c) const;
	//We do this because "minor" seems to be a macro somewhere
	#ifdef minor
	#undef minor
	#endif
	real minor   (const int& r, const int& c) const;

	real  maxAbs()             const;
	real  sumRow        (const int& r) const;
	real  sumAbsRow     (const int& r) const;
	real  sumColumn     (const int& c) const;
	real  sumAbsColumn  (const int& c) const;
	real  sumElements   ()             const;
	real  sumAbsElements()             const;
	real  trace         ()             const;
	real  determinant   ()             const;
	real  permanent     ()             const;

static Matrix Identity(const int& s);
static Matrix Scalar(const int& s, const real& k);
static Matrix Exchange(const int& s);
static Matrix Constant(const int& r, const int& c, const real& k);
static Matrix Constant(const int& s, const real& k) { return Constant(s, s, k); };
static Matrix Zero    (const int& r, const int& c)   { return Constant(r, c, 0.0e0); };
static Matrix Zero    (const int& s)                 { return Constant(s, s, 0.0e0); };
static Matrix Unit    (const int& r, const int& c)   { return Constant(r, c, 1.0e0); };
static Matrix Unit    (const int& s)                 { return Constant(s, s, 1.0e0); };

	Matrix transpose        () const;
	Matrix cofactor         () const;
	Matrix adjoint          () const;
	Matrix inverse          () const;
	Matrix symmetricPart    () const;
	Matrix antisymmetricPart() const;
	Matrix compound         (const int& k) const;

	// Dimension Tests
	bool isEmpty           ()             const { return (nrows == 0 && ncols == 0); };
	bool isSquare          ()             const { return (nrows == ncols); };
	bool isSquare          (const unsigned int& s) const { return (isSquare() && nrows == s); };
	bool isRectangular     ()             const { return (nrows != ncols); };
	bool isRowVector       ()             const { return (nrows == 1);     };
	bool isColumnVector    ()             const { return (ncols == 1);     };

	//Rectangular Matrices Tests
	bool isConstant          (const real& k) const; // All elements = k
	bool isConstant          () const { return isConstant(a[0][0]); };
	bool isZero              () const { return isConstant(0.0e0); };
	bool isUnit              () const { return isConstant(1.0e0); };
	bool isPositive          () const;
	bool isNonNegative       () const;
	bool isIncidence         () const;
	bool isAlternatingSign   () const;

	// Square Matrices Tests
	bool isDiagonal          () const { return lowerBandwidth() == 0 && upperBandwidth() == 0; };
	bool isIdentity          () const { return (isDiagonal() && mainDiagonal().isUnit()); };
	bool isScalar            () const { return (isDiagonal() && mainDiagonal().isConstant()); };
	bool isSignature         () const;
	bool isExchange          () const; // Como Identity pero con la antidiagonal

	bool isToeplitz          () const;
	bool isCirculant         () const;// Toeplitz y A[i][j] == (i - j) % n
	bool isHankel            () const;
	bool isHilbert           () const; // Hankel with a(i,j)=1/(i+j-1)

	// Triangular Matrices Tests
	// Lower = Left, Upper = Right
	// Unit = Normed
	// Atomic = Gauss (transformation)
	bool isUpperTriangular        () const { return lowerBandwidth() == 0; };
	bool isLowerTriangular        () const { return upperBandwidth() == 0; };
	bool isStrictlyUpperTriangular() const { return isUpperTriangular() && mainDiagonal().isZero(); };
	bool isStrictlyLowerTriangular() const { return isLowerTriangular() && mainDiagonal().isZero(); };
	bool isUnitUpperTriangular    () const { return isUpperTriangular() && mainDiagonal().isUnit(); };
	bool isUnitLowerTriangular    () const { return isLowerTriangular() && mainDiagonal().isUnit(); };
	bool isAtomicUpperTriangular  () const;
	bool isAtomicLowerTriangular  () const;
	bool isTriangular             () const { return isUpperTriangular() || isLowerTriangular();};
	bool isStrictlyTriangular     () const { return isTriangular() && mainDiagonal().isZero(); };
	bool isUnitTriangular         () const { return isTriangular() && mainDiagonal().isUnit(); };
	bool isAtomicTriangular       () const { return isAtomicUpperTriangular() || isAtomicLowerTriangular();};

	bool isUpperHessenberg   () const { return lowerBandwidth() <= 1; };
	bool isLowerHessenberg   () const { return upperBandwidth() <= 1; };
	bool isHessenberg        () const { return isUpperHessenberg() || isLowerHessenberg();};

	bool isUpperBidiagonal   () const { return isUpperTriangular() && isLowerHessenberg(); };
	bool isLowerBidiagonal   () const { return isLowerTriangular() && isUpperHessenberg(); };
	bool isBidiagonal        () const { return isUpperBidiagonal() || isLowerBidiagonal(); };

	bool isTridiagonal       () const { return isUpperHessenberg() && isLowerHessenberg(); };
	bool isJacobi            () const { return isTridiagonal(); };

	bool isSymmetric          () const { return (transpose() ==  (*this)); };
	bool isAntiSymmetric      () const { return (transpose() == -(*this)); };
	bool isCentroSymmetric    () const; // si A = J * A * J, J es exchange
	bool isCentroAntiSymmetric() const; // si A = - J * A * J, J es exchange
	bool isBiSymmetric        () const; // si A = A.transpose = J * A * J, J es exchange
	bool isPerSymmetric       () const; // si A = J * A.transpose * J, J es exchange
	bool isPerAntiSymmetric   () const; // si A = -J * A.transpose * J, J es exchange
	bool isSingular           () const { return (determinant() == 0.0e0); };
	bool isUnimodular         () const { return (determinant() == 1.0e0); };
	bool isInvertible         () const { return !isSingular(); };
	bool isDiagonallyDominant () const;
	bool isPositiveDefinite   () const { return mainDiagonal().isPositive() && isDiagonallyDominant() && transpose().isDiagonallyDominant(); };
	bool isStochastic         () const;
	bool isSubStochastic      () const;
	bool isDoublyStochastic   () const;
	bool isIdempotent         () const;
	bool isInvolutary         () const;
	bool isPermutation        () const; // One 1 in each row and each column (rest 0s)
	bool isOrthogonal         () const { return (transpose() * (*this)) == Matrix::Identity(rows()); };
	bool isProperOrthogonal   () const { return isOrthogonal() && determinant() ==  1.0e0; };
	bool isImproperOrthogonal () const { return isOrthogonal() && determinant() == -1.0e0; };
	bool isNormal             () const { return commutator((*this), transpose()).isZero(); };
	bool isVectorizedTranspose() const; // is the mn#mn  permutation matrix whose i,jth element is 1 if j=1+m(i-1)-(mn-1)floor((i-1)/n) or 0 otherwise

	bool isRightInverseOf      (const Matrix& A) const { return (A * (*this) == Identity(A.rows())); };
	bool isLeftInverseOf       (const Matrix& A) const { return ((*this) * A == Identity(A.columns())); };
	bool isInverseOf           (const Matrix& A) const { return isRightInverseOf(A) && isLeftInverseOf(A); };
	bool isGeneralizedInverseOf(const Matrix& A) const { return (A * (*this) * A == A); };
	bool isPseudoInverseOf     (const Matrix& A) const;

	template<class real2>
	friend ostream& operator<<(ostream& os, const Matrix<real2>& A);

	void LUdecompositionDoolittle(Matrix& L, Matrix& U) const;
	void LUdecompositionCrout    (Matrix& L, Matrix& U) const;
	void SVDdecomposition        (Matrix& U, Matrix& W, Matrix& V) const;
	Matrix forwardSubstitution(const Matrix& b) const;
	Matrix backSubstitution   (const Matrix& b) const;

	template<class real2>
	friend Matrix<real2> solve(const Matrix<real2>& A, const Matrix<real2>& B);
};

template <typename real = float>
class Vector : public Matrix<real>
{
public:
	Vector() : Matrix<real>() {}
	Vector(unsigned int n) : Matrix<real>(n,1) {}
	Vector(const Matrix<real>& m) : Matrix<real>(m) {}
	real operator()(unsigned int n) const { return ((Matrix<real>*)this)->operator()(n,0); }
	real& operator()(unsigned int n) { return ((Matrix<real>*)this)->operator()(n,0); }
	unsigned int size() const { return this->rows(); }
	void resize(unsigned int n) { this->Matrix<real>::resize(n,1); }
};


/*
Vector<double> operator*(const Vector<double>& v, float f)
{
	Vector<double> sol(v.rows());
	for (unsigned int i=0;i<v.rows();i++)
		sol(i) = f*v(i);
	return sol;
}

Vector<double> operator*(float f, const Vector<double>& v)
{
	Vector<double> sol(v.rows());
	for (unsigned int i=0;i<v.rows();i++)
		sol(i) = f*v(i);
	return sol;
}

Vector<float> operator*(const Vector<float>& v, double f)
{
	Vector<float> sol(v.rows());
	for (unsigned int i=0;i<v.rows();i++)
		sol(i) = f*v(i);
	return sol;
}

Vector<float> operator*(double f, const Vector<float>& v)
{
	Vector<float> sol(v.rows());
	for (unsigned int i=0;i<v.rows();i++)
		sol(i) = f*v(i);
	return sol;
}


template <typename real>
Vector<real> operator*(const Vector<real>& v, double f)
{
	Vector<real> sol(v.rows());
	for (unsigned int i=0;i<v.rows();i++)
		sol(i) = f*v(i);
	return sol;
}

template <typename real>
Vector<real> operator*(double f, const Vector<real>& v)
{
	Vector<real> sol(v.rows());
	for (unsigned int i=0;i<v.rows();i++)
		sol(i) = f*v(i);
	return sol;
}


template <typename real>
Vector<real> operator*(const Vector<real>& v, real f)
{
	Vector<real> sol(v.rows());
	for (unsigned int i=0;i<v.rows();i++)
		sol(i) = f*v(i);
	return sol;
}

template <typename real>
Vector<real> operator*(real f, const Vector<real>& v)
{
	Vector<real> sol(v.rows());
	for (unsigned int i=0;i<v.rows();i++)
		sol(i) = f*v(i);
	return sol;
}
*/

template <typename real>
real dot(const Vector<real>& v1, const Vector<real>& v2)
{
	return v1.trans_mult(v2)(0,0);
}

class Norms
{
public:
	enum Norm {NORM1,NORM2,NORMINF};
private:
	static Norm _norm;
public:
	static Norm norm(Norm __norm) { _norm = __norm; return _norm; } 
	static Norm norm() { return _norm; } 
};

Norms::Norm Norms::_norm = Norms::NORM2;

template <typename real>
real norm(const Vector<real>& v)
{
	switch (Norms::norm())
	{
	case Norms::NORM1: return v.sumAbsElements();
	case Norms::NORMINF: return v.maxAbs();
	case Norms::NORM2: 
	default:	return sqrt(v.trans_mult(v)(0,0));
	}
}

template <typename real>
const Matrix<real>& Matrix<real>::operator=(const Matrix<real>& that)
{
	copy(that);
	return *this;
}

template <typename real >
Matrix<real> Matrix<real>::operator+() const
{
	Matrix<real> A(*this);

	return A;
}

template <typename real >
Matrix<real> Matrix<real>::operator-() const
{
	Matrix<real> A(rows(), columns());
	for (unsigned int i = 0; i < elements(); i++)
		A.data[i] = - data[i];

	return A;
}

template <typename real >
Matrix<real> Matrix<real>::operator+(const Matrix<real>& that) const
{
	Matrix<real> A(rows(), columns());
	for (unsigned int i = 0; i < elements(); i++)
		A.data[i] = data[i] + that.data[i];

	return A;
}

template <typename real >
const Matrix<real>& Matrix<real>::operator+=(const Matrix<real>& that)
{
	for (unsigned int i = 0; i < elements(); i++)
		data[i] += that.data[i];

	return *this;
}

template <typename real>
Matrix<real> Matrix<real>::operator-(const Matrix<real>& that) const
{
	Matrix<real> A(rows(), columns());
	for (unsigned int i = 0; i < elements(); i++)
		A.data[i] = data[i] - that.data[i];

	return A;
}

template <typename real >
const Matrix<real>& Matrix<real>::operator-=(const Matrix<real>& that)
{
	for (unsigned int i = 0; i < elements(); i++)
		data[i] -= that.data[i];

	return *this;
}

template <typename real >
Matrix<real> Matrix<real>::operator*(const Matrix<real>& that) const
{
	Matrix<real> A(rows(), that.columns());
	unsigned int common = columns();
	for (unsigned int r = 0; r < A.rows(); r++)
	{
		for (unsigned int c = 0; c < A.columns(); c++)
		{
			A[r][c] = 0.0e0;
			for (unsigned int i = 0; i < common; i++)
				A[r][c] += a[r][i] * that[i][c];
		}
	}

	return A;
}

template <typename real >
const Matrix<real>& Matrix<real>::operator*=(const Matrix<real>& that)
{
	Matrix<real> tmp = (*this) * that;
	(*this) = tmp;

	return *this;
}

template <typename real>
Matrix<real> Matrix<real>::operator*(real k) const
{
	Matrix<real> A(rows(), columns());
	for (unsigned int i = 0; i < elements(); i++)
		A.data[i] = k * data[i];

	return A;
}

template <typename real>
const Matrix<real>& Matrix<real>::operator*=(real k)
{
	for (unsigned int i = 0; i < elements(); i++)
		data[i] *= k;

	return *this;
}

template <typename real>
Matrix<real> operator*(real k, const Matrix<real>& that)
{
	Matrix<real> A(that.rows(), that.columns());
	for (unsigned int i = 0; i < A.elements(); i++)
		A.data[i] = k * that.data[i];

	return A;
}

template <typename real>
Matrix<real> hadamardProduct(const Matrix<real>& A, const Matrix<real>& B)
{
	Matrix<real> C(A.rows(), A.columns());

	for (unsigned int i = 0; i < C.elements(); i++)
		C.data[i] = A.data[i] * B.data[i];

	return C;
}

template <typename real>
Matrix<real> kroneckerProduct(const Matrix<real>& A, const Matrix<real>& B)
{
	Matrix<real> C;

	for (unsigned int r = 0; r < A.rows(); r++)
	{
		Matrix<real> Crow;
		for (unsigned int c = 0; c < A.columns(); c++)
		{
			Matrix<real> aB = A[r][c] * B;
			Crow = concatenate(Crow, aB);
		}
		C = stack(C, Crow);
	}

	return C;
}

template <typename real>
Matrix<real> commutator(const Matrix<real>& A, const Matrix<real>& B)
{
	return (A * B) - (B * A);
}

template <typename real>
Matrix<real>   Matrix<real>::trans_mult  (const Matrix<real>& that) const
{
    return transpose()*that;
}

template <typename real>
bool homogeneus(const Matrix<real>& A, const Matrix<real>& B)
{
	if (equalSize(A, B))
	{
		Matrix<real> C(A.rows(), A.columns());
		for (unsigned int i = 0; i < C.elements(); i++)
			C.data[i] = A.data[i] / B.data[i];
		return !C.isZero() && C.isConstant();
	}
	else
		return false;
}

template <typename real>
bool equal(const Matrix<real>& A, const Matrix<real>& B)
{
	if (equalSize(A, B))
	{
		for (unsigned int i = 0; i < A.elements(); i++)
			if (A.data[i] != B.data[i])
				return false;
		return true;
	}
	else
		return false;
}

template <typename real>
bool equalSize(const Matrix<real>& A, const Matrix<real>& B)
{
	return (A.rows() == B.rows()) && (A.columns() == B.columns());
}

template <typename real>
bool compatible(const Matrix<real>& A, const Matrix<real>& B)
{
	return A.columns() == B.rows();
}

template <typename real>
void Matrix<real>::swapRows(const int& r1, const int& r2)
{
	real* temp;

	if (r1 != r2)
	{
		temp  = a[r1];
		a[r1] = a[r2];
		a[r2] = temp;
	}
}

template <typename real>
void Matrix<real>::swapColumns(const int& c1, const int& c2)
{
	real temp;

	if (c1 != c2)
	{
		for (unsigned int r = 0; r < rows(); r++)
		{
			temp     = a[r][c1];
			a[r][c1] = a[r][c2];
			a[r][c2] = temp;
		}
	}
}

template <typename real>
void Matrix<real>::addRowTo(const int& r1, const int& r2, const real& k)
{
	for (unsigned int c = 0; c < columns(); c++)
		a[r2][c] += k * a[r1][c];
}

template <typename real>
void Matrix<real>::addColumnTo(const int& c1, const int& c2, const real& k)
{
	for (unsigned int r = 0; r < rows(); r++)
		a[r][c2] += k * a[r][c1];
}

template <typename real>
void Matrix<real>::multiplyRowBy(const int& r, const real& k)
{
	if (k != 0.0e0)
	{
		for (unsigned int c = 0; c < columns(); c++)
			a[r][c] *= k;
	}
}

template <typename real>
void Matrix<real>::multiplyColumnBy(const int& c, const real& k)
{
	if (k != 0.0e0)
	{
		for (unsigned int r = 0; r < rows(); r++)
			a[r][c] *= k;
	}
}

template <typename real>
Matrix<real> Matrix<real>::rowVector(const int& r) const
{
	Matrix<real> A(1, columns());

	for (unsigned int j = 0; j < columns(); j++)
	{
		A[0][j] = a[r][j];
	}

	return A;
}

template <typename real>
Matrix<real> Matrix<real>::columnVector(const int& c) const
{
	Matrix<real> A(rows(), 1);

	for (unsigned int i = 0; i < rows(); i++)
	{
		A[i][0] = a[i][c];
	}

	return A;
}

template <typename real>
Matrix<real> Matrix<real>::eliminateRow(const int& r) const
{
	Matrix<real> A(rows() - 1, columns());
	unsigned int iA, i;
	unsigned int jA;
	for (iA = 0, i = 0; iA < A.rows(); iA++, i++)
	{
		if (i == r) i++;
		for (jA = 0; jA < A.columns(); jA++)
		{
			A[iA][jA] = a[i][jA];
		}
	}
	return A;
}

template <typename real>
Matrix<real> Matrix<real>::eliminateColumn(const int& c) const
{
	Matrix<real> A(rows(), columns() - 1);
	unsigned int iA;
	unsigned int jA, j;
	for (iA = 0; iA < A.rows(); iA++)
	{
		for (jA = 0, j = 0; jA < A.columns(); jA++, j++)
		{
			if (j == c) j++;
			A[iA][jA] = a[iA][j];
		}
	}

	return A;
}

template <typename real>
Matrix<real> Matrix<real>::eliminateElement(const int& r, const int& c) const
{
	Matrix<real> A(rows() - 1, columns() - 1);
	unsigned int i, iA;
	unsigned int j, jA;
	for (iA = 0, i = 0; iA < A.rows(); iA++, i++)
	{
		if (i == r) i++;
		for (jA = 0, j = 0; jA < A.columns(); jA++, j++)
		{
			if (j == c) j++;
			A[iA][jA] = a[i][j];
		}
	}

	return A;
}

template <typename real>
Matrix<real> concatenate(const Matrix<real>& AL, const Matrix<real>& AR)
{
	unsigned int i, j;
	Matrix<real> A(AL.isEmpty() ? AR.rows() : AL.rows(), AL.columns() + AR.columns());

	for (i = 0; i < A.rows(); i++)
	{
		for (j = 0; j < AL.columns(); j++)
		{
			A[i][j] = AL[i][j];
		}
		for (j = 0; j < AR.columns(); j++)
		{
			A[i][j + AL.columns()] = AR[i][j];
		}
	}

	return A;
}

template <typename real>
Matrix<real> stack(const Matrix<real>& AT, const Matrix<real>& AB)
{
	unsigned int i, j;
	Matrix<real> A(AT.rows() + AB.rows(), AT.isEmpty() ? AB.columns() : AT.columns());

	for (j = 0; j < A.columns(); j++)
	{
		for (i = 0; i < AT.rows(); i++)
		{
			A[i][j] = AT[i][j];
		}
		for (i = 0; i < AB.rows(); i++)
		{
			A[i + AT.rows()][j] = AB[i][j];
		}
	}

	return A;
}

template <typename real>
Matrix<real> Matrix<real>::mainDiagonal(const int& d) const
{
	Matrix<real> D(1, columns() - abs(d));
	int r = 0, c = 0;
	if      (d > 0) r += d;
	else if (d < 0) c -= d;

	for (unsigned int i = 0; i < D.columns(); i++)
		D[0][i] = a[r + i][c + i];

	return D;
}

template <typename real>
Matrix<real> Matrix<real>::antiDiagonal(const int& d) const
{
	Matrix<real> D(1, columns() - fabs(d));

	unsigned int r = columns() - 1, c = 0;
	if      (d > 0) c += d;
	else if (d < 0) r += d;

	for (unsigned int i = 0; i < D.columns(); i++)
		D[0][i] = a[r - i][c + i];

	return D;
}

template <typename real>
int Matrix<real>::upperBandwidth() const
{
	unsigned int p;
	for (p = rows() - 1; p > 0; p--)
		if (!mainDiagonal(-p).isZero())
			return p;

	return 0;
}

template <typename real>
int Matrix<real>::lowerBandwidth() const
{
	unsigned int p;

	for (p = rows() - 1; p > 0; p--)
		if (!mainDiagonal(p).isZero())
			return p;

	return 0;
}

template <typename real>
real Matrix<real>::conditionNumber() const
{
	Matrix<real> U, W, V;
	SVDdecomposition(U, W, V);
	real maxSV = W[0][0], minSV = W[0][0];
	for (unsigned int i = 1; i < W.rows(); i++)
	{
		maxSV = max(maxSV, W[i][i]);
		minSV = min(minSV, W[i][i]);
	}
	return maxSV/minSV;
}

template <typename real>
real  Matrix<real>::sumRow(const int& r) const
{
	real k = 0.0e0;

	for (unsigned int c = 0; c < columns(); c++)
		k += a[r][c];

	return k;
}

template <typename real>
real  Matrix<real>::sumAbsRow(const int& r) const
{
	real k = 0.0e0;

	for (unsigned int c = 0; c < columns(); c++)
		k += fabs(a[r][c]);

	return k;
}

template <typename real>
real  Matrix<real>::sumColumn(const int& c) const
{
	real k = 0.0e0;

	for (unsigned int r = 0; r < rows(); r++)
		k += a[r][c];

	return k;
}

template <typename real>
real  Matrix<real>::sumAbsColumn(const int& c) const
{
	real k = 0.0e0;

	for (unsigned int r = 0; r < rows(); r++)
		k += fabs(a[r][c]);

	return k;
}

template <typename real>
real Matrix<real>::sumElements()const
{
	real k = 0.0e0;

	for (unsigned int i = 0; i < elements(); i++)
		k += data[i];

	return k;
}

template <typename real>
real Matrix<real>::sumAbsElements()const
{
	real k = 0.0e0;

	for (unsigned int i = 0; i < elements(); i++)
		k += fabs(data[i]);

	return k;
}

template <typename real>
real Matrix<real>::maxAbs()const
{
	real k = 0.0e0;

	for (unsigned int i = 0; i < elements(); i++)
		k = data[i]>k?data[i]:k;

	return k;
}

template <typename real>
real  Matrix<real>::trace() const
{
	real k = 0.0e0;

	if (isSquare())
	{
		for (unsigned int i = 0; i < rows(); i++)
			k += a[i][i];
	}

	return k;
}

template <typename real>
real  Matrix<real>::determinant() const
{
	real det = 0.0e0;

	if (isSquare(1))
	{
		det = a[0][0];
	}
	else if (isSquare())
	{
		for (unsigned int i = 0; i < columns(); i++)
		{
			det += a[0][i] * cofactor(0, i);
		}
	}
	return det;
}

template <typename real>
real  Matrix<real>::permanent() const
{
	real per = 0.0e0;

	if (isSquare(1))
	{
		per = a[0][0];
	}
	else if (isSquare())
	{
		for (unsigned int i = 0; i < columns(); i++)
		{
			per += a[0][i] * minor(0, i);
		}
	}
	return per;
}

template <typename real>
real Matrix<real>::minor(const int& r, const int& c) const
{
	return eliminateElement(r, c).determinant();
}

template <typename real>
real Matrix<real>::cofactor(const int& r, const int& c) const
{
	if ((r + c) % 2)
		return - minor(r, c);
	else
		return   minor(r, c);
}

template <typename real>
Matrix<real> Matrix<real>::Scalar(const int& s, const real& k)
{
	Matrix<real> A(s, s);

	for (unsigned int r = 0; r < A.rows(); r++)
		for (unsigned int c = 0; c < A.columns(); c++)
				A[r][c] = (r == c) ? k : 0.0e0;

	return A;
}

template <typename real>
Matrix<real> Matrix<real>::Identity(const int& s)
{
	Matrix<real> A(s, s);

	for (unsigned int r = 0; r < A.rows(); r++)
		for (unsigned int c = 0; c < A.columns(); c++)
				A[r][c] = (r == c) ? 1.0e0 : 0.0e0;

	return A;
}

template <typename real>
Matrix<real> Matrix<real>::Exchange(const int& s)
{
	Matrix<real> A(s, s);

	for (unsigned int r = 0; r < A.rows(); r++)
		for (unsigned int c = 0; c < A.columns(); c++)
				A[r][c] = (r + c == A.rows()) ? 1.0e0 : 0.0e0;

	return A;
}

template <typename real>
Matrix<real> Matrix<real>::Constant(const int& r, const int& c, const real& k)
{
	Matrix<real> A(r, c);

	for (unsigned int i = 0; i < A.elements(); i++)
		A.data[i] = k;

	return A;
}


template <typename real>
Matrix<real> Matrix<real>::transpose() const
{
	Matrix<real> A(columns(), rows());

	for (unsigned int r = 0; r < rows(); r++)
		for (unsigned int c = 0; c < columns(); c++)
			A[c][r] = a[r][c];

	return A;
}

template <typename real>
Matrix<real> Matrix<real>::cofactor() const
{
	Matrix<real> A(rows(), columns());

	for (unsigned int r = 0; r < rows(); r++)
		for (unsigned int c = 0; c < columns(); c++)
			A[r][c] = cofactor(r, c);

	return A;
}

template <typename real>
Matrix<real> Matrix<real>::adjoint() const
{
	return cofactor().transpose();
};

template <typename real>
Matrix<real> Matrix<real>::inverse() const
{
	#if 0

	return (1.0f / determinant()) * adjoint();

	#else
	#if 0

	// Gauss-Jordan Elimination
	int i,icol,irow,j,k,l,ll;
	real big,dum,pivinv;

	// The inverse
	Matrix<real> A(*this);
	// The solution
	Matrix<real> B = Matrix<real>::Identity(rows());

	int n = A.rows();
	int m = B.columns();
	vector<int> indxc(n), indxr(n), ipiv(n);
	for (j = 0; j < n; j++) ipiv[j] = 0;
	for (i = 0; i < n; i++)
	{
		big = 0.0e0;
		for (j = 0; j < n; j++)
			if (ipiv[j] != 1)
				for (k = 0; k < n; k++)
				{
					if (ipiv[k] == 0)
					{
						if (fabs(A[j][k]) >= big)
						{
							big  = fabs(A[j][k]);
							irow = j;
							icol = k;
						}
					}
				}
		++(ipiv[icol]);
		if (irow != icol)
		{
			for (l = 0; l < n; l++) swap(A[irow][l], A[icol][l]);
			for (l = 0; l < m; l++) swap(B[irow][l], B[icol][l]);
		}
		indxr[i] = irow;
		indxc[i] = icol;
		if (A[icol][icol] == 0.0e0) cout<<"gaussj: Singular Matrix<real>\n";
		pivinv = 1.0e0 / A[icol][icol];
		A[icol][icol] = 1.0e0;
		for (l  = 0; l  < n; l++) A[icol][l] *= pivinv;
		for (l  = 0; l  < m; l++) B[icol][l] *= pivinv;
		for (ll = 0; ll < n; ll++)
			if (ll != icol)
			{
				dum = A[ll][icol];
				A[ll][icol] = 0.0e0;
				for (l = 0; l < n; l++) A[ll][l] -= A[icol][l] * dum;
				for (l = 0; l < m; l++) B[ll][l] -= B[icol][l] * dum;
			}
	}
	for (l = n - 1; l >= 0; l--)
	{
		if (indxr[l] != indxc[l])
			for (k = 0; k < n; k++)
				swap(A[k][indxr[l]], A[k][indxc[l]]);
	}

	return A;

	#else

	// LU decomposition
	Matrix<real> L, U, B_error;
	Matrix<real> B = Identity(rows());
	Matrix<real> x2improve, x, z, x_prev, x_error;

	real error_prev, error;

	if (isInvertible())
	{
		LUdecompositionCrout(L, U);
		z = L.forwardSubstitution(B);
		x = U.backSubstitution(z);


		B_error = ((*this) * x) - B;
		error   = B_error.sumAbsElements();
		int iter    = 0;
		int maxiter = 100;
		while ( !(((*this) * x) == B))
		{
			if (iter >= maxiter)
				break;
			x_prev     = x;
			error_prev = error;

			B_error = ((*this) * x) - B;

			error      = B_error.sumAbsElements();
			//cout << error << endl;
			if (error > error_prev)
			{
				x = x_prev;
				break;
			}

			z       = L.forwardSubstitution(B_error);
			x_error = U.backSubstitution(z);
			x -= x_error;

			//cout << x - x_prev << endl;
			if (x == x_prev) break;
			iter++;
		}
		//cout << error << endl<<endl;
	}

	return x;

	#endif
	#endif
};

template <typename real>
Matrix<real> solve(const Matrix<real>& A, const Matrix<real>& B)
{
	Matrix<real> L, U, B_error;
	Matrix<real> x, z;

//	Matrix<real> x_prev, x_error;

//	real error_prev, error;

//	LOG_INFO("Solving Linear System ...");

//	if (A.isInvertible())
	{
//		LOG_INFO("    LU decomposition ...");
		A.LUdecompositionCrout(L, U);
//		LOG_INFO("    forward substitution ...");
		z = L.forwardSubstitution(B);
//		LOG_INFO("    back substitution ...");
		x = U.backSubstitution(z);


//		LOG_INFO("    Improving solution ...");

/*		B_error = (A * x) - B;
		error   = B_error.sumAbsElements();
		int iter    = 0;
		int maxiter = 100;
		while ( !((A * x) == B))
		{
			if (iter >= maxiter)
				break;
			x_prev     = x;
			error_prev = error;

			B_error = (A * x) - B;

			error      = B_error.sumAbsElements();
			//cout << error << endl;
			if (error > error_prev)
			{
				x = x_prev;
				break;
			}

			z       = L.forwardSubstitution(B_error);
			x_error = U.backSubstitution(z);
			x -= x_error;

			//cout << x - x_prev << endl;
			if (x == x_prev) break;
			iter++;
		}
		//cout << error << endl<<endl;*/
	}

	return x;
}

template <typename real>
Matrix<real> Matrix<real>::symmetricPart() const
{
	Matrix<real> As;

	if (isSquare())
		As = 0.5e0 * ((*this) + transpose());

	return As;
}

template <typename real>
Matrix<real> Matrix<real>::antisymmetricPart() const
{
	Matrix<real> Aa;

	if (isSquare())
		Aa = 0.5e0 * ((*this) - transpose());

	return Aa;
}

template <typename real>
bool Matrix<real>::isConstant(const real& k) const
{
	for (unsigned int i = 0; i < elements(); i++)
	{
		if (data[i] != k)
			return false;
	}
	return true;
}

template <typename real>
bool Matrix<real>::isPositive() const
{
	for (unsigned int i = 0; i < elements(); i++)
		if (data[i] <= 0.0e0)
			return false;
	return true;
}

template <typename real>
bool Matrix<real>::isNonNegative() const
{
	for (unsigned int i = 0; i < elements(); i++)
		if (data[i] < 0.0e0)
			return false;
	return true;
}

template <typename real>
bool Matrix<real>::isIncidence() const
{
	for (unsigned int i = 0; i < elements(); i++)
		if (data[i] != 0.0e0 && data[i] != 1.0e0)
			return false;
	return true;
}

template <typename real>
bool Matrix<real>::isAlternatingSign() const
{
	for (unsigned int i = 0; i < elements(); i++)
		if (data[i] != 0.0e0 && data[i] != 1.0e0 && data[i] != -1.0e0)
			return false;
	for (unsigned int i = 0; i < rows(); i++)
		if (sumRow(i) != 1.0e0)
			return false;
	for (unsigned int i = 0; i < columns(); i++)
		if (sumColumn(i) != 1.0e0)
			return false;

	return true;
}

template <typename real>
bool Matrix<real>::isSignature() const
{
	if (!isDiagonal())
		return false;

	Matrix<real> d = mainDiagonal();
	for (unsigned int i = 0; i < d.elements(); i++)
		if (d.data[i] != 1.0e0 && d.data[i] != -1.0e0)
			return false;

	return true;
}

template <typename real>
bool Matrix<real>::isToeplitz() const
{
	int p;

	for (p = rows() - 1; p > - rows(); p--)
		if (!mainDiagonal(p).isConstant())
			return false;

	return true;
}

template <typename real>
bool Matrix<real>::isHankel() const
{
	int p;

	for (p = rows() - 1; p > - rows(); p--)
		if (!antiDiagonal(p).isConstant())
			return false;

	return true;
}

template <typename real>
bool Matrix<real>::isAtomicUpperTriangular() const
{
	if (!isUnitUpperTriangular())
		return false;

	int nzc = 0;
	for (unsigned int c = 1; c < columns(); c++)
	{
		int nz = 0;
		for (unsigned int r = 0; r < c; r++)
		{
			if (a[r][c] != 0.0e0)
				nz++;
		}
		if (nz > 0)
			nzc++;
	}

	return (nzc == 1);
}

template <typename real>
bool Matrix<real>::isAtomicLowerTriangular() const
{
	if (!isUnitLowerTriangular())
		return false;

	int nzc = 0;
	for (unsigned int c = 0; c < columns(); c++)
	{
		int nz = 0;
		for (unsigned int r = c + 1; r < rows(); r++)
		{
			if (a[r][c] != 0.0e0)
				nz++;
		}
		if (nz > 0)
			nzc++;
	}

	return (nzc == 1);
}

template <typename real>
bool Matrix<real>::isDiagonallyDominant() const
{
	for (unsigned int r = 0; r < rows(); r++)
	{
		real sum = 0.0e0;
		for (unsigned int c = 0; c < columns(); c++)
			if (c != r)
				sum += fabs(a[r][c]);
		if (fabs(a[r][r]) <= sum)
			return false;
	}

	return true;

}

template <typename real>
bool Matrix<real>::isStochastic() const
{
	if (!isNonNegative())
		return false;

	for (unsigned int i = 0; i < rows(); i++)
		if (sumRow(i) != 1.0e0)
			return false;

	return true;
}

template <typename real>
bool Matrix<real>::isSubStochastic() const
{
	if (!isNonNegative())
		return false;

	for (unsigned int i = 0; i < rows(); i++)
		if (sumRow(i) > 1.0e0)
			return false;

	return true;
}

template <typename real>
bool Matrix<real>::isDoublyStochastic() const
{
	if (!isNonNegative())
		return false;

	for (unsigned int i = 0; i < rows(); i++)
		if (sumRow(i) != 1.0e0)
			return false;
	for (unsigned int i = 0; i < columns(); i++)
		if (sumColumn(i) != 1.0e0)
			return false;

	return true;
}

template <typename real>
bool Matrix<real>::isIdempotent() const
{
	Matrix<real> A;

	A = (*this) * (*this);

	return (A == (*this));
}

template <typename real>
bool Matrix<real>::isInvolutary() const
{
	Matrix<real> A;

	A = (*this) * (*this);

	return A.isIdentity();
}

template <typename real>
bool Matrix<real>::isPseudoInverseOf(const Matrix<real>& A) const
{
	Matrix<real> AAplus = A * (*this);
	Matrix<real> AplusA = (*this) * A;
	return (
		  isGeneralizedInverseOf(A) &&
		A.isGeneralizedInverseOf(*this) &&
		AAplus.transpose() == AAplus &&
		AplusA.transpose() == AplusA
	);
}

template <typename real>
bool RothsRemovalRule(const Matrix<real>& A, const Matrix<real>& X, const Matrix<real>& B, const Matrix<real>& C)
{
	return ((A * X - X * B) == C);
}

template <typename real>
ostream& operator<<(ostream& os,const Matrix<real>& A)
{
	os.precision(3);
//	os << "[ ";
//	for (unsigned int c = 0; c < A.columns(); c++)
//			os << "        " << " ";
//	os << "]" << endl;
	for (unsigned int r = 0; r < A.rows(); r++)
	{
		os << "[ ";
		for (unsigned int c = 0; c < A.columns(); c++)
			os << setw(8) << fixed << right <<  A[r][c] << " ";
		os << "]" << endl;
	}
//	os << "\xC0 ";
//	for (unsigned int c = 0; c < A.columns(); c++)
//			os << "        " << " ";
//	os << "\xD9" << endl;

	return os;
}

template <typename real>
void Matrix<real>::LUdecompositionDoolittle(Matrix<real>& L, Matrix<real>& U) const
{
	int n = rows();
	L = Zero(n);
	U = Zero(n);
	real temp;

	for (unsigned int k = 0; k < n; k++)
	{
		L[k][k] = 1.0e0;
		temp = 0.0e0;
		for (unsigned int s = 0; s < k; s++)
			temp += L[k][s] * U[s][k];
		U[k][k] = a[k][k] - temp;

		for(unsigned int i = k + 1; i < n; i++)
		{
			temp = 0.0e0;
			for (unsigned int s = 0; s < k; s++)
				temp += L[i][s] * U[s][k];
			L[i][k] = (a[i][k] - temp) / U[k][k];
		}

		for(unsigned int i = k + 1; i < n; i++)
		{
			temp = 0.0e0;
			for (unsigned int s = 0; s < k; s++)
				temp += L[k][s] * U[s][k];
			U[k][i] = (a[k][i] - temp) / L[k][k];
		}
	}
}

template <typename real>
void Matrix<real>::LUdecompositionCrout(Matrix<real>& L, Matrix<real>& U) const
{
	int n = rows();
	L = Zero(n);
	U = Zero(n);
	real temp;

	for (unsigned int k = 0; k < n; k++)
	{
		U[k][k] = 1.0e0;
		temp = 0.0e0;
		for (unsigned int s = 0; s < k; s++)
			temp += L[k][s] * U[s][k];
		L[k][k] = a[k][k] - temp;

		for(unsigned int i = k + 1; i < n; i++)
		{
			temp = 0.0e0;
			for (unsigned int s = 0; s < k; s++)
				temp += L[i][s] * U[s][k];
			L[i][k] = (a[i][k] - temp) / U[k][k];
		}

		for(unsigned int i = k + 1; i < n; i++)
		{
			temp = 0.0e0;
			for (unsigned int s = 0; s < k; s++)
				temp += L[k][s] * U[s][k];
			U[k][i] = (a[k][i] - temp) / L[k][k];
		}
	}
}

template <typename real>
real SIGN(const real &a, const double &b)
{
	return b >= 0 ? (a >= 0 ? a : -a) : (a >= 0 ? -a : a);
}

template <typename real>
real SQR(const real a)
{
	return a*a;
}


template <typename real>
real pythag(const real a, const real b)
{
	// computes c = sqrt(a^2+b^2) without destructive underflow or overflow
	real absa,absb;

	absa=fabs(a);
	absb=fabs(b);
	if (absa > absb) return absa*sqrt(1.0+SQR(absb/absa));
	else return (absb == 0.0 ? 0.0 : absb*sqrt(1.0+SQR(absa/absb)));
}

template <typename real>
void Matrix<real>::SVDdecomposition(Matrix<real>& U, Matrix<real>& W, Matrix<real>& V) const
{
	bool flag;
	int i,its,j,jj,k,l=0,nm;
	real anorm,c,f,g,h,s,scale,x,y,z;

	int m=rows();
	int n=columns();

	U = (*this);
	W = Zero(n);
	V = Zero(n);

	vector<real> rv1(n);
	g=scale=anorm=0.0;
	for (i=0;i<n;i++) {
		l=i+2;
		rv1[i]=scale*g;
		g=s=scale=0.0;
		if (i < m) {
			for (k=i;k<m;k++) scale += fabs(U[k][i]);
			if (scale != 0.0) {
				for (k=i;k<m;k++) {
					U[k][i] /= scale;
					s += U[k][i]*U[k][i];
				}
				f=U[i][i];
				g = -SIGN(sqrt(s),f);
				h=f*g-s;
				U[i][i]=f-g;
				for (j=l-1;j<n;j++) {
					for (s=0.0,k=i;k<m;k++) s += U[k][i]*U[k][j];
					f=s/h;
					for (k=i;k<m;k++) U[k][j] += f*U[k][i];
				}
				for (k=i;k<m;k++) U[k][i] *= scale;
			}
		}
		W[i][i]=scale *g;
		g=s=scale=0.0;
		if (i+1 <= m && i != n) {
			for (k=l-1;k<n;k++) scale += fabs(U[i][k]);
			if (scale != 0.0) {
				for (k=l-1;k<n;k++) {
					U[i][k] /= scale;
					s += U[i][k]*U[i][k];
				}
				f=U[i][l-1];
				g = -SIGN(sqrt(s),f);
				h=f*g-s;
				U[i][l-1]=f-g;
				for (k=l-1;k<n;k++) rv1[k]=U[i][k]/h;
				for (j=l-1;j<m;j++) {
					for (s=0.0,k=l-1;k<n;k++) s += U[j][k]*U[i][k];
					for (k=l-1;k<n;k++) U[j][k] += s*rv1[k];
				}
				for (k=l-1;k<n;k++) U[i][k] *= scale;
			}
		}
		anorm=max(anorm,(fabs(W[i][i])+fabs(rv1[i])));
	}
	for (i=n-1;i>=0;i--) {
		if (i < n-1) {
			if (g != 0.0) {
				for (j=l;j<n;j++)
					V[j][i]=(U[i][j]/U[i][l])/g;
				for (j=l;j<n;j++) {
					for (s=0.0,k=l;k<n;k++) s += U[i][k]*V[k][j];
					for (k=l;k<n;k++) V[k][j] += s*V[k][i];
				}
			}
			for (j=l;j<n;j++) V[i][j]=V[j][i]=0.0;
		}
		V[i][i]=1.0;
		g=rv1[i];
		l=i;
	}
	for (i=min(m,n)-1;i>=0;i--) {
		l=i+1;
		g=W[i][i];
		for (j=l;j<n;j++) U[i][j]=0.0;
		if (g != 0.0) {
			g=1.0/g;
			for (j=l;j<n;j++) {
				for (s=0.0,k=l;k<m;k++) s += U[k][i]*U[k][j];
				f=(s/U[i][i])*g;
				for (k=i;k<m;k++) U[k][j] += f*U[k][i];
			}
			for (j=i;j<m;j++) U[j][i] *= g;
		} else for (j=i;j<m;j++) U[j][i]=0.0;
		++U[i][i];
	}
	for (k=n-1;k>=0;k--) {
		for (its=0;its<30;its++) {
			flag=true;
			for (l=k;l>=0;l--) {
				nm=l-1;
				if (fabs(rv1[l])+anorm == anorm) {
					flag=false;
					break;
				}
				if (fabs(W[nm][nm])+anorm == anorm) break;
			}
			if (flag) {
				c=0.0;
				s=1.0;
				for (i=l-1;i<k+1;i++) {
					f=s*rv1[i];
					rv1[i]=c*rv1[i];
					if (fabs(f)+anorm == anorm) break;
					g=W[i][i];
					h=pythag(f,g);
					W[i][i]=h;
					h=1.0/h;
					c=g*h;
					s = -f*h;
					for (j=0;j<m;j++) {
						y=U[j][nm];
						z=U[j][i];
						U[j][nm]=y*c+z*s;
						U[j][i]=z*c-y*s;
					}
				}
			}
			z=W[k][k];
			if (l == k) {
				if (z < 0.0) {
					W[k][k] = -z;
					for (j=0;j<n;j++) V[j][k] = -V[j][k];
				}
				break;
			}
			if (its == 29) throw("No convergence in 30 svdcmp iterations");
			x=W[l][l];
			nm=k-1;
			y=W[nm][nm];
			g=rv1[nm];
			h=rv1[k];
			f=((y-z)*(y+z)+(g-h)*(g+h))/(2.0*h*y);
			g=pythag(f,(real)1.0);
			f=((x-z)*(x+z)+h*((y/(f+SIGN(g,f)))-h))/x;
			c=s=1.0;
			for (j=l;j<=nm;j++) {
				i=j+1;
				g=rv1[i];
				y=W[i][i];
				h=s*g;
				g=c*g;
				z=pythag(f,h);
				rv1[j]=z;
				c=f/z;
				s=h/z;
				f=x*c+g*s;
				g=g*c-x*s;
				h=y*s;
				y *= c;
				for (jj=0;jj<n;jj++) {
					x=V[jj][j];
					z=V[jj][i];
					V[jj][j]=x*c+z*s;
					V[jj][i]=z*c-x*s;
				}
				z=pythag(f,h);
				W[j][j]=z;
				if (z) {
					z=1.0/z;
					c=f*z;
					s=h*z;
				}
				f=c*g+s*y;
				x=c*y-s*g;
				for (jj=0;jj<m;jj++) {
					y=U[jj][j];
					z=U[jj][i];
					U[jj][j]=y*c+z*s;
					U[jj][i]=z*c-y*s;
				}
			}
			rv1[l]=0.0;
			rv1[k]=f;
			W[k][k]=x;
		}
	}
}

template <typename real>
Matrix<real> Matrix<real>::forwardSubstitution(const Matrix<real>& b) const
{
	Matrix<real> x;
	if (b.rows() == rows() && isLowerTriangular())
	{
		x = Zero(b.rows(), b.columns());

		for (unsigned int i = 0; i < x.rows(); i++)
		{
			for (unsigned int j = 0; j < x.columns(); j++)
			{
				real temp = 0.0e0;
				for (unsigned int k = 0; k < i; k++)
					temp += a[i][k] * x[k][j];
				x[i][j] = (b[i][j] - temp) / a[i][i];
			}
		}
	}
	return x;
}

template <typename real>
Matrix<real> Matrix<real>::backSubstitution(const Matrix<real>& b) const
{
	Matrix<real> x;

	if (b.rows() == rows() && isUpperTriangular())
	{
		x = Zero(b.rows(), b.columns());

		for (unsigned int i = x.rows() - 1; i >= 0; i--)
		{
			for (unsigned int j = 0; j < x.columns(); j++)
			{
				real temp = 0.0e0;
				for (unsigned int k = i + 1; k < x.rows(); k++)
					temp += a[i][k] * x[k][j];
				x[i][j] = (b[i][j] - temp) / a[i][i];
			}
		}
	}

	return x;
}



#endif

