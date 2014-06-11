/*
 * DataManager.cpp
 *
 *  Created on: 2010-1-6
 *      Author: zhaoqi
 */

#include "DataManager.h"
#include "Utility.h"
#include <opencv/highgui.h>
#include <iostream>
#include <fstream>
//DataManager DataManager::m_globalDM;

DataManager::DataManager(){

}

void DataManager::rgb2chrom(mat_3f& mat) {
	cv::Size imgSize = mat.size();
	for (int i = 0; i < imgSize.height; i++)
		for (int j = 0; j < imgSize.width; j++) {
			cv::Vec3f& val = mat(i, j);
			float norm = cv::norm(val);
			norm = norm > 1e-8 ? 1/norm : 0;

			val[0] *= norm;
			val[1] *= norm;
			val[2] *= norm;
		}

}

void interpValue(mat_3f mat, mat_u& mask, int py,int px, int winSz)
{

	int w = mat.size().width;
	int h = mat.size().height;
	cv::Vec3f avgVal(0,0,0);
	int cnt = 0;
	for (int i = -winSz/2; i <= winSz/2; i++)
	{
		for (int j=-winSz/2; j <= winSz/2; j++)
		{
			int y = py + i;
			int x = px + j;
			if (y <0 || y >= h || x < 0|| x >= w ||!mask(y,x) ||(i == 0 && j == 0))
			{
				continue;
			}
			if (mat(y,x)[0] != mat(y,x)[0] || mat(y,x)[1] != mat(y,x)[1] || mat(y,x)[2] != mat(y,x)[2])
			{
				continue;
			}

			avgVal += mat(y,x);
			cnt++;
		}
	}
	avgVal[0] /= cnt;
	avgVal[1] /= cnt;
	avgVal[2] /= cnt;
	mat(py,px) = avgVal;

}

void DataManager::normalizeImage2(mat_3f& mat,mat_u& m_mask){
	//
	int iw = mat.size().width;
	int ih = mat.size().height;
	float avgInt = 0;
	if (m_mask.size().width == 0)
	{
		m_mask = mat_u(ih,iw);
		m_mask = 255;
	}

	//cv::imshow("before",mat);
	//cv::imshow("mask",m_mask);
	//cv::waitKey(0);


	float nzCnt = 0;
	for (int i = 0; i < ih; i++)
	{
		for (int j = 0; j < iw; j++)
		{
			if (!m_mask(i,j))
			{
				continue;
			}
			cv::Vec3f& val = mat(i,j);
			bool invalidVal = false;

			for (int k = 0; k < 3; k++)
			{
				if (val[k] != val[k]) //1.INF value detected
				{

					//std::cout << " inf detected" << std::endl;
					invalidVal = true;
					//getchar();
				}
				if (val[k] < 0)
				{
					invalidVal = true;
					//std::cout <<"negative number" << std::endl;
					//val[k] = 0.5;
				}

			}
			if (invalidVal)
			{
				//val[0] = val[1] = val[2] = 0.5;
				interpValue(mat,m_mask,i,j,5);
			}

			nzCnt ++;
			avgInt += val[0];
			avgInt += val[1];
			avgInt += val[2];
		}

	}


	avgInt /= (nzCnt * 3); //average value
	float magFac = 3;
	float maxVal = magFac * avgInt;
	float maxVal2 = -1;

	for (int i = 0; i < ih; i++)
	{
		for (int j = 0; j < iw; j++)
		{
			cv::Vec3f& val = mat(i,j);
			for (int k = 0; k < 3; k++)
			{
				if (val[k] > maxVal2&& val[k] < maxVal)
				{
					maxVal2 = val[k];
				}
				if (val[k] >= maxVal)
				{
					cv::Vec3f avgVec(0,0,0);
					for (int k1 = -1; k1 <= 1; k1++)
					{
						for (int k2 = -1; k2 <= 1; k2++)
						{
							if (k1 == 0 && k2 == 0)
							{
								continue;
							}

							int cy = i + k1;
							int cx = j + k2;
							if (cx<0 || cx >= iw || cy <0 || cy >= ih)
							{
								continue;
							}
							avgVec += mat(cy,cx);
						}
					}
					mat(i,j)[k] = avgVec[k] / 8;
				}
			}
		}
	}

	//std::cout <<"maximum val:" << maxVal2 << std::endl;
	maxVal2 = maxVal2 > 1e-8 ? 1/maxVal2: 0;
	mat *= maxVal2;

}

void DataManager::normalizeImage(mat_3f& mat,mat_u& mask) {
	//float gMax = -1;
	//cv::Size imgSize = mat.size();
	//for(int i=0; i<imgSize.height;i++){
	//	for(int j=0;j<imgSize.width;j++){
	//		cv::Vec3f& pixVal = mat(i,j);

	//		if (pixVal[0] > gMax)
	//		{
	//			gMax = pixVal[0];
	//		}
	//		if (pixVal[1] > gMax)
	//		{
	//			gMax = pixVal[1];
	//		}
	//		if (pixVal[2] > gMax)
	//		{
	//			gMax = pixVal[2];
	//		}
	//		//float norm = cv::norm(pixVal);
	//		//if( norm > gMax)
	//		//	gMax = norm;
	//	}
	//}
	//std::cout << "max: " << gMax << std::endl;
	//gMax = gMax > 1e-8 ? 1.0 / gMax : 0;
	//mat *= gMax;
	normalizeImage2(mat,mask);
}

void DataManager::savePixelGroup(std::string& fileName){
	FILE* fid = fopen(fileName.c_str(),"wb");
	if(!fid){
		std::cerr << "failed to open:" << fileName << std::endl;
		return;
	}
	int pgCnt = m_pgVec.size();
	fwrite(&pgCnt,sizeof(pgCnt),1,fid);
	for(int i=0; i<pgCnt; i++){
		PixelGroup& tmpPg = m_pgVec[i];
		tmpPg.writeToFile(fid);
	}
	fclose(fid);
}
void DataManager::loadPixelGroup(std::string& fileName){
	FILE* fid = fopen(fileName.c_str(),"rb");
	if(!fid){
		std::cerr << "failed to open:" << fileName << std::endl;
		return;
	}
	int pgCnt;
	fread(&pgCnt,sizeof(pgCnt),1,fid);
	for(int i=0; i< pgCnt; i++){
		PixelGroup tmpPg;
		tmpPg.readFromFile(fid);
		m_pgVec.push_back(tmpPg);
	}
	fclose(fid);
}

void  DataManager::erodeBinaryImage(mat_f img){
	//
	mat_f kMat(5,5);
	mat_f dstImg = img.clone();
	kMat = 1.0;
	cv::erode(img,dstImg,kMat,cv::Point(-1,-1),1);
	//cv::imshow("src",img);
	//cv::imshow("dst",dstImg);
	//cv::waitKey(0);
	dstImg.copyTo(img);

}

#define __SR_ONLY__ //save shading and reflectance only
void DataManager::saveResult(std::string basePath, std::string baseName) {

	mat_3f inputClone = m_inputImg * 255.0;
	mat_3f chromClone = m_chromImg * 255.0;
	mat_3f shadingClone = m_shadingImg * 255.0;
	mat_3f albedoClone = m_albedoImg * 255.0;
	mat_f sErrClone = m_shadeErr * 255.0;
	mat_f rErrClone = m_refErr * 255.0;
	mat_f iErrClone = m_intErr * 255.0;
	///save paths
	std::string inputSavePath = basePath + baseName +".png";
	std::string chromSavePath = basePath + baseName +"_chrom.png";
	std::string shadingSavePath = basePath + baseName + "_shading.png";
	std::string albedoSavePath = basePath + baseName +"_albedo.png";
	std::string sErrImgPath = basePath + baseName + "_sErr.png";
	std::string sErrDataPath = basePath + baseName + "_sErr.txt";
	std::string rErrImgPath = basePath + baseName + "_rErr.png";
	std::string rErrDataPath = basePath + baseName + "_rErr.txt";
	std::string iErrImgPath = basePath + baseName + "_iErr.png";
	std::string iErrDataPath = basePath + baseName + "_iErr.txt";
	std::string srMaskSavePath = basePath + baseName + "_srMask.png";
	std::string pgSavePath = basePath + baseName + "_pg.bin";
#ifdef __SR_ONLY__
	cv::imwrite(shadingSavePath,shadingClone);
	cv::imwrite(albedoSavePath,albedoClone);
#else
	///begin to save
	cv::imwrite(inputSavePath,inputClone);
	cv::imwrite(chromSavePath,chromClone);
	cv::imwrite(shadingSavePath,shadingClone);
	cv::imwrite(albedoSavePath,albedoClone);
	cv::imwrite(sErrImgPath,sErrClone);
	cv::imwrite(rErrImgPath,rErrClone);
	cv::imwrite(iErrImgPath,iErrClone);
	cv::imwrite(srMaskSavePath,m_srMask);
	savePixelGroup(pgSavePath);
	//write err data as txt file
	std::ofstream of;
	of.open(sErrDataPath.c_str(),std::ios_base::out);
	of << m_shadeErr;
	of.close();
	of.open(rErrDataPath.c_str(),std::ios_base::out);
	of << m_refErr;
	of.close();
	of.open(iErrDataPath.c_str(),std::ios_base::out);
	of << m_intErr;
	of.close();
#endif

}

void DataManager::init(mat_3f& inputImg, mat_u* maskPtr) {
	m_inputImg = inputImg.clone();
	m_imgSize = inputImg.size();
	m_chromImg = inputImg.clone();
	m_shadingImg.create(m_imgSize);
	m_shadingImg = cv::Vec3f(0, 0, 0);
	m_albedoImg.create(m_imgSize);
	m_albedoImg = cv::Vec3f(0, 0, 0);
	m_shadeErr = mat_f(m_imgSize);
	m_shadeErr = 0;
	m_refErr = mat_f(m_imgSize);
	m_refErr = 0;
	m_intErr = mat_f(m_imgSize);
	m_intErr = 0;
	m_srMask = mat_u(m_imgSize);//
	m_srMask = 0; //set to zero

	if (maskPtr) {
		m_mask = maskPtr->clone();
	} else {
		m_mask.create(m_imgSize);
		m_mask = 255;
	}
	//
	rgb2chrom(m_chromImg);
	m_pixVec.clear();
	m_pixVec.resize(m_imgSize.width * m_imgSize.height);
	m_pgVec.clear();
}

DataManager::~DataManager() {
	// TODO Auto-generated destructor stub
}
