#ifndef __UBLAS_H__
#define __UBALS_H__

#include <boost/numeric/ublas/matrix.hpp> 
#include <boost/numeric/ublas/vector.hpp> 
#include <boost/numeric/ublas/io.hpp>
#include <boost/numeric/ublas/matrix_sparse.hpp>
#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/vector.hpp>

namespace ublas = boost::numeric::ublas;
using namespace boost::numeric::ublas;
typedef ublas::matrix<float> ublas_mat_f; 



//typedef ublas::coordinate_matrix<float> ublas_smat_f;
typedef ublas::mapped_matrix<float> ublas_mm_f;
typedef ublas::compressed_matrix<float,ublas::column_major>  ublas_cm_f;
typedef ublas::vector<float> ublas_vec_f;
typedef ublas::compressed_vector<float> ublas_svec_f;

#endif