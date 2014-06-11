/*
 * GraphCut.h
 *
 * Wrapper for Weksler Olga's GraphCut to Matlab
 *
 * wrapper by Shai Bagon 2006, contact shai.abgon@weizmann.ac.il or shaibagon@gmail.com
 *
 */
#ifndef _GRAPH_CUT_H_
#define _GRAPH_CUT_H_

#include "mex.h"
#include <tmwtypes.h>

/* handle type for graph class */
typedef void* GraphHandle;

/* we want to verify that the class is valid */
#define VALID_CLASS_SIGNITURE   0xabcd0123

/* pointer types in 64 bits machines */
#ifdef A64BITS
#define MATLAB_POINTER_TYPE mxUINT64_CLASS
#else
#define MATLAB_POINTER_TYPE mxUINT32_CLASS
#endif

template<class T>
void GetScalar(const mxArray* x, T& scalar)
{
    if ( mxGetNumberOfElements(x) != 1 )
        mexErrMsgIdAndTxt("GraphCut:GetScalar","input is not a scalar!");
    void *p = mxGetData(x);
    switch (mxGetClassID(x)) {
        case mxCHAR_CLASS:
            scalar = *(char*)p;
            break;
        case mxDOUBLE_CLASS:
            scalar = *(double*)p;
            break;
        case mxSINGLE_CLASS:
            scalar = *(float*)p;
            break;
        case mxINT8_CLASS:
            scalar = *(char*)p;
            break;
        case mxUINT8_CLASS:
            scalar = *(unsigned char*)p;
            break;
        case mxINT16_CLASS:
            scalar = *(short*)p;
            break;
        case mxUINT16_CLASS:
            scalar = *(unsigned short*)p;
            break;
        case mxINT32_CLASS:
            scalar = *(int*)p;
            break;
        case mxUINT32_CLASS:
            scalar = *(unsigned int*)p;
            break;
#ifdef A64BITS            
        case mxINT64_CLASS:
            scalar = *(int64_T*)p;
            break;
        case mxUINT64_CLASS:
            scalar = *(uint64_T*)p;
            break;
#endif /* 64 bits machines */            
        default:
            mexErrMsgIdAndTxt("GraphCut:GetScalar","unsupported data type");
    }
}

/* memory allocations - redirect to MATLAB memory menager */
void* operator new(size_t size);
void* operator new[](size_t size);
void operator delete(void* ptr);
void operator delete[](void* ptr);

#endif /* _GRAPH_CUT_H_ */
