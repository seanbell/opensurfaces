#include "Matlab.h"
#include "Timer.h"
#include <iostream>
#include <cstdio>
void MatLab::putSparseMatrix(ublas_cm_f& sm, char* matVarName){
	typedef ublas_cm_f::iterator1 it1_t; 
	typedef ublas_cm_f::iterator2 it2_t;
	std::vector<int> ridxVec;
	std::vector<int> cidxVec;
	std::vector<float> mValVec;
	ublas_cm_f& resultMat = sm;
	for (it2_t it1 = resultMat.begin2();it1 != resultMat.end2(); it1++)
	{
		int idx1, idx2;
		for (it1_t it2 = it1.begin(); it2 != it1.end(); it2++)
		{
			idx1 = it2.index1();
			idx2 = it2.index2();
			float eleVal = resultMat(idx1,idx2);
			ridxVec.push_back(idx1);
			cidxVec.push_back(idx2);
			mValVec.push_back(eleVal);
		}
	}
	int nzCnt = ridxVec.size();

	double *mData = new double[3 * nzCnt];
	for (int i = 0; i < nzCnt * 3; i+=3)
	{
		mData[i] = ridxVec[i/3];
		mData[i+1] = cidxVec[i/3];
		mData[i+2] = mValVec[i/3];
	}

	mxArray* mArray = mxCreateDoubleMatrix(3,nzCnt,mxREAL);
	memcpy((void*)mxGetPr(mArray),(void*)mData,sizeof(double)*3*nzCnt);
	engPutVariable(m_pEngine,"consMat",mArray);
	int pixCnt = resultMat.size1();
	char buffer[512];
	sprintf(buffer,"%s = sparse(consMat(1,:)+1,consMat(2,:)+1,consMat(3,:),%d,%d);",matVarName,pixCnt,pixCnt);
	engEvalString(m_pEngine,buffer); //create the sparse matrix
	mxDestroyArray(mArray);
	delete[] mData;
	//
}

void MatLab::putSparseMatrix(SparseMat& tcm,char* matVarName){
	//
	std::vector<int> ridxVec;
	std::vector<int> cidxVec;
	std::vector<double> mValVec;
	for (int i = 0; i < tcm.m_dim1; i++)
	{
		Slot& slot = tcm.getRow(i);
		for (int j = 0; j < slot.size(); j++)
		{	
			ridxVec.push_back(i);
			cidxVec.push_back(slot[j].m_idx);
			mValVec.push_back(slot[j].m_val);
		}
	}

	int nzCnt = ridxVec.size();

	std::cout <<"nzCnt:" << nzCnt << std::endl;
	double *mData = new double[3 * nzCnt];
	for (int i = 0; i < nzCnt; i++)
	{
		mData[i * 3] = ridxVec[i];
		mData[i * 3 + 1] = cidxVec[i];
		mData[i * 3 + 2] = mValVec[i];
	}

	std::cout << "create array" << std::endl;
	mxArray* mArray = mxCreateDoubleMatrix(3,nzCnt,mxREAL);
	memcpy((void*)mxGetPr(mArray),(void*)mData,sizeof(double)*3*nzCnt);

	std::cout << "put variable" << std::endl;
	engPutVariable(m_pEngine,"consMat",mArray);
	int pixCnt = tcm.m_dim1;
	char buffer[512];
	std::cout << "construct sparse" << std::endl;
	sprintf(buffer,"%s = sparse(consMat(1,:)+1,consMat(2,:)+1,consMat(3,:),%d,%d);",matVarName,pixCnt,pixCnt);
	engEvalString(m_pEngine,buffer); //create the sparse matrix
	mxDestroyArray(mArray);
	delete[] mData;
}

void MatLab::putVec(db_vec& vec,char* matVarName){
	double *data = new double[vec.size()];
	for (int i = 0;i < vec.size(); i++)
	{
		data[i] = vec[i];
	}
	mxArray* vecArray = mxCreateDoubleMatrix(vec.size(),1,mxREAL);
	memcpy((void*)mxGetPr(vecArray),(void*)data,sizeof(double) * vec.size());
	engPutVariable(m_pEngine,matVarName,vecArray);
	delete[] data;
	mxDestroyArray(vecArray);

}

void MatLab::putVec(ublas_vec_f& vec,char* matVarName){
	double *data = new double[vec.size()];
	for (int i = 0;i < vec.size(); i++)
	{
		data[i] = vec(i);
	}
	mxArray* vecArray = mxCreateDoubleMatrix(vec.size(),1,mxREAL);
	memcpy((void*)mxGetPr(vecArray),(void*)data,sizeof(double) * vec.size());
	engPutVariable(m_pEngine,matVarName,vecArray);
	delete[] data;
	mxDestroyArray(vecArray);
}


//solve the sparse linear equation by matlab back-slash operator
//#define __CG__
ublas_vec_f MatLab::sparseLinSolve(ublas_cm_f& sm, ublas_vec_f& b){
	//
	MatLab& ml = MatLab::ref();
	Timer tick;
	tick.start();
	ml.putSparseMatrix(sm,"sm");
	m_matrixTime = tick.stop();
	ml.putVec(b,"b");
	tick.start();
#ifndef __CG__
	engEvalString(m_pEngine,"x = mldivide(sm,b);");
#else
	char buffer[512];
	int eleCnt = sm.size1();
	sprintf(buffer,"x = pcg(sm,b,1e-6,%d);",eleCnt);
	engEvalString(m_pEngine,buffer);
#endif
	tick.stop();
	m_linSolveTime = tick.getElapse();
	std::cout << "left divide:" << m_linSolveTime << std::endl;
	mxArray* xArray = engGetVariable(m_pEngine,"x");
	double* xData = mxGetPr(xArray);
	ublas_vec_f xVec(b);
	for (int i = 0; i < b.size(); i++)
	{
		xVec(i) = xData[i];
	}
	mxDestroyArray(xArray);
	return xVec;
}


void MatLab::spmVecProd(SparseMat& sp,db_vec& vec, db_vec& vec1){
	//
	vec1 = vec;
	putSparseMatrix(sp,"A");
	putVec(vec,"x");
	engEvalString(m_pEngine,"rv = A * x;");
	mxArray* rvArray = engGetVariable(m_pEngine,"rv");
	double* rvData = mxGetPr(rvArray);
	for (int i = 0; i < vec.size(); i++)
	{
		vec1[i] = rvData[i];
	}
	//
}

void MatLab::spmspmProd(SparseMat& sp1, SparseMat& sp2,SparseMat& rsp){
	//
	std::cout << "putting variable" << std::endl;
	putSparseMatrix(sp1,"sp1");
	putSparseMatrix(sp2,"sp2");
	std::cout << "sparse matrix multiplication" << std::endl;
	engEvalString(m_pEngine,"rsp = sp1 * sp2;");
	std::cout << "locating non-zero elements" << std::endl;
	engEvalString(m_pEngine,"[i,j,v] = find(rsp);");
	engEvalString(m_pEngine,"[nzcnt,tmp] = size(i);");
	mxArray* nzcntArray = engGetVariable(m_pEngine,"nzcnt");
	double* nzcntData = mxGetPr(nzcntArray);
	int nzcnt = (int) nzcntData[0];
	std::cout << "nzcnt:" << nzcnt << std::endl;
	mxArray* iArray = engGetVariable(m_pEngine,"i");
	double* iData = mxGetPr(iArray);

	mxArray* jArray = engGetVariable(m_pEngine,"j");
	double* jData = mxGetPr(jArray);

	mxArray* vArray = engGetVariable(m_pEngine,"v");
	double* vData = mxGetPr(vArray);

	rsp.reset(sp1.m_dim1,sp2.m_dim2);
	for (int i = 0; i < nzcnt; i++)
	{
		rsp.addElement(iData[i] - 1, jData[i] - 1, vData[i]);
	}
	std::cout << "merge" << std::endl;
	rsp.merge();
}

db_vec MatLab::sparseLinSolve(SparseMat& sm,db_vec& b){
	//
	ublas_vec_f b1(b.size());
	for (int i= 0; i < b.size(); i++)
	{
		b1(i) = b[i];
	}
	ublas_vec_f res = sparseLinSolve(sm,b1);
	db_vec res1(res.size());
	for (int i = 0; i < res.size() ;i++)
	{
		res1[i] = res(i);
	}
	return res1;
}
ublas_vec_f MatLab::sparseLinSolve(SparseMat& sm, ublas_vec_f& b){

	MatLab& ml = MatLab::ref();
	Timer tick;
	tick.start();
	ml.putSparseMatrix(sm,"sm");
	m_matrixTime = tick.stop();
	ml.putVec(b,"b");
	tick.start();
#ifndef __CG__
	engEvalString(m_pEngine,"x = mldivide(sm,b);");
#else
	char buffer[512];
	int eleCnt = sm.size1();
	sprintf(buffer,"x = pcg(sm,b,1e-6,%d);",eleCnt);
	engEvalString(m_pEngine,buffer);
#endif
	tick.stop();
	m_linSolveTime = tick.getElapse();
	std::cout << "left divide:" << m_linSolveTime << std::endl;
	mxArray* xArray = engGetVariable(m_pEngine,"x");
	double* xData = mxGetPr(xArray);
	ublas_vec_f xVec(b);
	for (int i = 0; i < b.size(); i++)
	{
		xVec(i) = xData[i];
	}
	mxDestroyArray(xArray);
	return xVec;
}

void MatLab::evalCmd(std::string cmd){
	engEvalString(m_pEngine,cmd.c_str());
}

ublas_vec_f MatLab::getVec(std::string varName, int sz){
	mxArray* tmpArray = engGetVariable(m_pEngine,varName.c_str());
	double* tmpData = mxGetPr(tmpArray);
	ublas_vec_f tmpVec(sz);
	for (int i = 0; i < sz; i++)
	{
		tmpVec(i) = tmpData[i];
	}
	mxDestroyArray(tmpArray);
	return tmpVec;
}

mat_3f MatLab::getImage(std::string path,int h, int w){
	char buffer[512];
	std::string varName = "tmp_cv_img";
	sprintf(buffer,"%s = imread('%s')",varName.c_str(), path.c_str());
	evalCmd(buffer);
	sprintf(buffer,"%s = im2double(%s)",varName.c_str(),varName.c_str());
	evalCmd(buffer);
	//evalCmd("imshow(tmp_cv_img)");

	ublas_vec_f imgVec = getVec(varName, h * w * 3);
	mat_3f img(w,h);
	int planeStep  = w * h;
	for (int i = 0; i < w; i++)
	{
		for (int j = 0; j < h; j++)
		{
			float r = imgVec(i * h + j);
			float g = imgVec(i * h + j + planeStep);
			float b = imgVec(i * h + j + 2 * planeStep);
			img(i,j) = cv::Vec3f(b,g,r);
		}
	}
	return img.t();
}
