#if 0
#include "PerformanceEval.h"
#include "Matlab.h"
//#include "IntrinsicMG.h"
//#define  __TEST_LMSE__

void PerformanceEvaluator::eval(){
	//float baseTrd = 0.00001;
	//float mag = 2.0;
	//int paraCnt = 10;
	//std::vector<float> chromTrd;
	//for (int i = 0; i < paraCnt; i++)
	//{
	//	chromTrd.push_back(baseTrd);
	//	baseTrd *= mag;

	//}
	//mat_3f bestShade,bestRef;
	//int bestIdx = -1;
	//float minLMSE;
	//char buffer[512];
	//std::string modeName[] = {
	//	"N",
	//	"Y",
	//};
	//for (int i = 0; i < m_objectPaths.size(); i++)
	//{
	//	std::string fullPath = m_objectPaths[i];
	//	std::string basePath, imgName, imgExt;
	//	Utility::pathDecompose(fullPath,basePath,imgName,imgExt);
	//	mat_3f inputImg = cv::imread(fullPath);
	//	inputImg /= 255.0;
	//	PyramidIntrinsic* imPtr = new PyramidIntrinsic(inputImg,3,2,NULL,NULL,NULL,"RI",true);
	//	imPtr->addAbsShadeScrib(imPtr->genAbsShadeCons(1.0));
	//	//create result director for current image
	//	std::string resultDir = m_resultRootPath + "/" + imgName;
	//	CreateDirectory(resultDir.c_str(),NULL);
	//	int imgNum = 0;
	//	
	//	for (int k = 0; k < 2; k++)
	//	{
	//		sprintf_s(buffer,"%s/%s_err_%s.txt",resultDir.c_str(),imgName.c_str(),modeName[k].c_str());
	//		FILE* errFID = fopen(buffer,"w");
	//		fprintf(errFID,"image size: %d x %d\n",inputImg.size().height,inputImg.size().width);
	//		if (k == 1)
	//		{
	//			imPtr->addAlbedoScrib(imPtr->genConsAlbedoCons(IMConfig::distThrd,IMConfig::txVar));
	//			imPtr->saveAlbedoConsVis(resultDir,imgName);
	//		}
	//		for (int j = 0; j < paraCnt; j++,imgNum++)
	//		{
	//			IMConfig::chromThrd = chromTrd[j]; //change the chromacity threshold

	//			imPtr->setLocalWindowSize(3);
	//			imPtr->init(); //window size
	//			imPtr->solve();

	//			imPtr->decompose(true,true,false);
	//			mat_3f estSd = imPtr->m_dm.getShading();
	//			mat_3f estRef = imPtr->m_dm.getAlbedo();

	//			fprintf(errFID,"Image Num:%4d\n",imgNum);
	//			fprintf(errFID,"chromacity threshod:%f\n",chromTrd[j]);
	//			fprintf(errFID,"tx variance:%f\n", IMConfig::txVar);
	//			fprintf(errFID,"tx dist thrd:%f\n",IMConfig::distThrd);
	//			fprintf(errFID,"matrix sparsity:%f\n",imPtr->m_sparsity);
	//			fprintf(errFID,"Run time:%.4f s\n",imPtr->m_solveTime);
	//			fprintf(errFID,"\n\n");
	//			sprintf_s(buffer,"%s_%f_%f_%f_%s",imgName.c_str(),IMConfig::chromThrd,IMConfig::txVar,IMConfig::distThrd,modeName[k].c_str());
	//			imPtr->saveResult(resultDir,buffer); //save the result as well 
	//		}
	//		fclose(errFID);
	//	}
	//	delete imPtr;
	//}
}

void PerformanceEvaluator::testThrd(){
	//
	std::string thrdPath = m_inputRootPath + "/" + "thrd.txt";
	FILE* thrdFid = fopen(thrdPath.c_str(),"r");
	std::vector<float> thrdVec;
	for(int i =0 ; i < m_objectPaths.size(); i++){
		float tmpThrd;
		fscanf(thrdFid,"%f",&tmpThrd);
		thrdVec.push_back(tmpThrd);
	}
	fclose(thrdFid);
	char buffer[512];
	std::string modeName[] = {
		"N",
		"Y",
	};
	std::string sumFile = m_resultRootPath + "/" + "resultSum.txt";
	FILE* sumFid = fopen(sumFile.c_str(),"w");
	for (int i = 0; i < m_objectPaths.size(); i++)
	{
		std::string basePath, imgName, imgExt;
		Utility::pathDecompose(m_objectPaths[i],basePath,imgName,imgExt);
		std::cout << "current object:" << imgName << std::endl;
		fprintf(sumFid,"%s\t",imgName.c_str());
		CreateDirectory((m_resultRootPath + "/" + imgName).c_str(),NULL); //
		std::string objResultPath = m_resultRootPath + "/" + imgName;
		std::string fullPath = m_objectPaths[i] + "/diffuse.png";
		Utility::pathDecompose(fullPath,basePath,imgName,imgExt);
		std::string maskPath1 = basePath + "/" + "mask.png";
		//std::string maskPath2 = basePath + "/" + "mask_1.png";
		std::string gtShadePath = basePath + "/" + "shading.png";
		std::string gtRefPath = basePath + "/" + "reflectance.png";
		std::string resultFilePath  = basePath + "/" + "err.txt";

		mat_3f inputImg1 = cv::imread(fullPath);
		int w = inputImg1.size().width;
		int h = inputImg1.size().height;
		mat_3f inputImg = MatLab::ref().getImage(fullPath,h,w);
		mat_3f mask1 = cv::imread(maskPath1);
		mask1 /= 255.0;
		mat_3f gtSdImg = cv::imread(gtShadePath);
		gtSdImg /= 255.0;
		mat_3f gtRefImg = MatLab::ref().getImage(gtRefPath,h,w);

		RetinexIntrinsic* imPtr = new RetinexIntrinsic(inputImg);
		imPtr->setROIMask(mask1);
		imPtr->addAbsShadeScrib(imPtr->genAbsShadeCons(0.7));
		int imgNum = 0;
		for (int k = 0; k < 2; k++)
		{
			if (k == 1)
			{
				imPtr->addAlbedoScrib(imPtr->genConsAlbedoCons(IMConfig::distThrd,IMConfig::txVar));
			}
			IMConfig::chromThrd = thrdVec[i];
			imPtr->init(); //window size
			imPtr->solve();

			imPtr->decompose(true,true);
			imPtr->saveResult(objResultPath,imgName);
			mat_3f estSd = imPtr->m_dm.getShading();
			mat_3f estRef = imPtr->m_dm.getAlbedo();

			float tmpLMSE = scoreImg(estSd,estRef,gtSdImg,gtRefImg,mask1);
			fprintf(sumFid,"%f\t",tmpLMSE);

			sprintf_s(buffer,"%s/%s_sd_%d.png",objResultPath.c_str(),imgName.c_str(),imgNum);
			cv::imwrite(buffer,estSd * 255.0);
			sprintf_s(buffer,"%s/%s_ref_%d.png",objResultPath.c_str(),imgName.c_str(),imgNum);
			cv::imwrite(buffer,estRef * 255.0);
		}
		fprintf(sumFid,"\r\n");
		delete imPtr;
	}
	fclose(sumFid);
}


#define  __USE_RI__
void PerformanceEvaluator::mitEval(){
	//
	float chromTrd[] = {0.00001,0.00002,0.00004,0.00008,0.00016,0.00032,0.00064,0.001, 0.002,0.003,0.004,0.005};
	//int paraCnt = sizeof(chromTrd)/ sizeof(float);
	int paraCnt = 1;
	mat_3f bestShade,bestRef;
	int bestIdx = -1;
	float minLMSE;
	char buffer[512];
	std::string modeName[] = {
		"N",
		"Y",
	};
	float thrd[] = {0.0007,
		0.0009,
		0.0003,
		0.0005,
		0.0003,
		0.0009,
		0.0003,
		0.0001,
		0.0007,
		0.0009,
		0.0009,
		0.0001,
		0.0003,
		0.0005,
		0.0003,
		0.0009};
	std::string sumFile = m_resultRootPath + "/" + "resultSum.txt";
	FILE* sumFid = fopen(sumFile.c_str(),"w");
	for (int i = 0; i < m_objectPaths.size(); i++)
	{
		std::string basePath, imgName, imgExt;
		Utility::pathDecompose(m_objectPaths[i],basePath,imgName,imgExt);
		fprintf(sumFid,"%s\t",imgName.c_str());
		CreateDirectory((m_resultRootPath + "/" + imgName).c_str(),NULL); //
		std::string objResultPath = m_resultRootPath + "/" + imgName;
		std::string fullPath = m_objectPaths[i] + "/diffuse.png";
		Utility::pathDecompose(fullPath,basePath,imgName,imgExt);
		std::string maskPath1 = basePath + "/" + "mask.png";
		//std::string maskPath2 = basePath + "/" + "mask_1.png";
		std::string gtShadePath = basePath + "/" + "shading.png";
		std::string gtRefPath = basePath + "/" + "reflectance.png";
		std::string resultFilePath  = basePath + "/" + "err.txt";

		mat_3f inputImg1 = cv::imread(fullPath);
		int w = inputImg1.size().width;
		int h = inputImg1.size().height;
		mat_3f inputImg = MatLab::ref().getImage(fullPath,h,w);
		mat_3f mask1 = cv::imread(maskPath1);
		mask1 /= 255.0;
		mat_3f gtSdImg = cv::imread(gtShadePath);
		gtSdImg /= 255.0;
		mat_3f gtRefImg = MatLab::ref().getImage(gtRefPath,h,w);

#ifdef __USE_RI__
		RetinexIntrinsic* imPtr = new RetinexIntrinsic(inputImg);
#else
		PyramidIntrinsic* imPtr = new PyramidIntrinsic(inputImg,3,1,NULL,NULL,NULL,"RI",FALSE);
#endif
		//set the mask which will be propagated to downsampled layers
		//imPtr->setLocalWindowSize(3);
		imPtr->setROIMask(mask1);
		//imPtr->setFeatureMask(mask2);
		imPtr->addAbsShadeScrib(imPtr->genAbsShadeCons(0.7));
		int imgNum = 0;
		for (int k = 0; k < 2; k++)
		{
			sprintf_s(buffer,"%s/%s_err_%s.txt",objResultPath.c_str(),imgName.c_str(),modeName[k].c_str());
			FILE* errFID = fopen(buffer,"w");
			fprintf(errFID,"image size: %d x %d\n",inputImg.size().height,inputImg.size().width);
#ifdef  __USE_RI__
			if (k == 1)
			{
				imPtr->addAlbedoScrib(imPtr->genConsAlbedoCons(IMConfig::distThrd,IMConfig::txVar));
			}
#else
			if (k == 0)
			{
				imPtr->m_genCons = false; 
			}
			else
				imPtr->m_genCons = true;

#endif	
			minLMSE = 100;
			for (int j = 0; j < 12; j++,imgNum++)
			{

				IMConfig::chromThrd = chromTrd[j];
#ifdef __USE_RI__
				imPtr->setChromThrd(IMConfig::chromThrd);
#endif
				imPtr->init(); //window size
				imPtr->solve();

				imPtr->decompose(true,true);
				imPtr->saveResult(objResultPath,imgName);
				mat_3f estSd = imPtr->m_dm.getShading();
				mat_3f estRef = imPtr->m_dm.getAlbedo();

				float tmpLMSE = scoreImg(estSd,estRef,gtSdImg,gtRefImg,mask1);
				fprintf(sumFid,"%f ",tmpLMSE);
				fprintf(errFID,"Image Num:%4d\n",imgNum);
				fprintf(errFID,"chromacity threshod:%f\n",chromTrd[j]);
				fprintf(errFID,"tx variance:%f\n", IMConfig::txVar);
				fprintf(errFID,"tx dist thrd:%f\n",IMConfig::distThrd);
				fprintf(errFID,"LMSE:%f\n",tmpLMSE);
				fprintf(errFID,"sparsity:%f\n",imPtr->m_sparsity);
				fprintf(errFID,"Run time:%.4f s\n",imPtr->m_solveTime);
				fprintf(errFID,"\n\n");

				sprintf_s(buffer,"%s/%s_sd_%d.png",objResultPath.c_str(),imgName.c_str(),imgNum);
				cv::imwrite(buffer,estSd * 255.0);
				sprintf_s(buffer,"%s/%s_ref_%d.png",objResultPath.c_str(),imgName.c_str(),imgNum);
				cv::imwrite(buffer,estRef * 255.0);

				if (tmpLMSE < minLMSE)
				{
					bestShade = estSd.clone();
					bestRef = estRef.clone();
					bestIdx = j;
					minLMSE = tmpLMSE;
				}
			}


			//now save the best decomposition
			std::cout << "writing best result" << std::endl;
			std::cout << "best idx:"<< bestIdx << std::endl;
			fprintf(errFID,"\n\n");
			fprintf(errFID,"chromacity threshod:%f\n",chromTrd[bestIdx]);
			fprintf(errFID,"tx variance:%f\n", IMConfig::txVar);
			fprintf(errFID,"tx dist thrd:%f\n",IMConfig::distThrd);
			fprintf(errFID,"LMSE:%f\n",minLMSE);
			fclose(errFID);
			sprintf_s(buffer,"%s/%s_sd_%s_est.png",objResultPath.c_str(),imgName.c_str(),modeName[k].c_str());
			cv::imwrite(buffer,bestShade * 255.0);
			sprintf_s(buffer,"%s/%s_ref_%s_est.png",objResultPath.c_str(),imgName.c_str(),modeName[k].c_str());
			cv::imwrite(buffer,bestRef * 255.0);
			std::cout << fullPath << ":" << minLMSE << std::endl;
			fprintf(sumFid,"\r\n");
		}
		delete imPtr;
	}
	fclose(sumFid);
}
void PerformanceEvaluator::evaluate(std::string methodName){
	if (m_mitData)
	{
		mitEval();
	}
	else{
		//
		eval();
	}
}

mat_f PerformanceEvaluator::rgb2gray(mat_3f img){
	mat_f grayFImg(img.size());
	for (int i = 0; i < img.size().height; i++)
	{
		for (int j = 0; j < img.size().width; j++)
		{
			grayFImg(i,j) = cv::norm(img(i,j));
		}
	}
	return grayFImg;
}

mat_f PerformanceEvaluator::mask2float(mat_u msk){
	mat_f fMsk(msk.size());
	fMsk = 0;
	for (int i = 0; i < msk.size().height; i++)
	{
		for (int j = 0; j < msk.size().width; j++)
		{
			if (msk(i,j))
			{
				fMsk(i,j) = 1.0;
			}
		}
	}
	return fMsk;
}

float PerformanceEvaluator::MSE(mat_f correct,mat_f estimate, mat_f fMsk){
	mat_f m1(correct.size());
	cv::multiply(correct,estimate,m1);
	mat_f tmp(correct.size());
	cv::multiply(fMsk,m1,tmp);
	float prod1 = cv::sum(tmp).val[0];
	mat_f m2(correct.size());
	cv::multiply(estimate,estimate,m2);
	cv::multiply(m2,fMsk,tmp);
	float prod2 = cv::sum(tmp).val[0];
	float alpha = (prod2 > 1e-5? prod1 / prod2 : 0);
	estimate *= alpha;
	mat_f diff = estimate - correct;
	mat_f diff2(correct.size());
	cv::multiply(diff,diff,diff2);
	mat_f mskDiff2(correct.size());
	cv::multiply(diff2,fMsk,mskDiff2);
	return cv::sum(mskDiff2).val[0];
}



mat_f getLocal(mat_f input,int y , int x, int winSz){
	mat_f lMat(winSz,winSz);
	for (int i = y; i < y + winSz; i++)
	{
		for (int j = x; j < x + winSz; j++)
		{
			lMat(i - y, j - x) = input(i,j);
		}
	}
	return lMat;
}

float PerformanceEvaluator::LMSE(mat_3f estImg, mat_3f gtImg, mat_3f msk, int winSize){
	int w = estImg.size().width;
	int h = estImg.size().height;
	int shift = winSize / 2;
	mat_f blkEst(winSize,winSize);
	blkEst = 0;

	mat_f fEst = rgb2gray(estImg);
	mat_f fGt = rgb2gray(gtImg);
	mat_f fMsk = rgb2gray(msk);
	float curSSQ = 0, total = 0;
	for (int i = 0; i < h - winSize; i+= shift)
	{
		for (int j = 0; j < w - winSize; j+= shift)
		{
			mat_f curGt = getLocal(fGt,i,j,winSize);
			mat_f curEst = getLocal(fEst,i,j,winSize);
			mat_f curMsk = getLocal(fMsk,i,j,winSize);
			float tmpE = MSE(curGt,curEst,curMsk);
			curSSQ += tmpE;
			tmpE = MSE(curGt,blkEst,curMsk);
			total += tmpE;
		}
	}
	return curSSQ / total;
}


float PerformanceEvaluator::scoreImg(mat_3f estSd,mat_3f estRef, mat_3f gtSd, mat_3f gtRef, mat_3f msk){
	//

	int winSize = 20;
	return 0.5 * LMSE(estSd,gtSd,msk,winSize) + 0.5 * LMSE(estRef,gtRef,msk,winSize);
}

std::vector<std::string> PerformanceEvaluator::loadExpConfig(std::string imgListPath){
	FILE* fid = fopen(imgListPath.c_str(),"r");
	if (!fid)
	{
		std::cerr << "Failed to open the image list file" << std::endl;
		return m_objectPaths;
	}
	char buffer[512];
	fscanf(fid,"%s",buffer);
	if (std::string(buffer) == "MIT")
	{
		m_mitData = true;
	}
	//first line is the input data root path
	fscanf(fid,"%s",buffer);
	m_inputRootPath = buffer;
	fscanf(fid,"%s",buffer);
	m_resultRootPath = buffer;
	//now read the image list
	while (true)
	{
		fscanf(fid,"%s",buffer);
		if (feof(fid))
		{
			break;
		}
		m_objectPaths.push_back(m_inputRootPath + "/" + std::string(buffer)); //image full path
	}
	std::cout <<"input data dir:" << m_inputRootPath << std::endl;
	std::cout <<"result data dir:" << m_resultRootPath <<std::endl;
	std::cout <<"# of images to handle:" << m_objectPaths.size() << std::endl;
	return m_objectPaths;
}


#endif
