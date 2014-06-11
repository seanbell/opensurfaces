/*
* main.cpp
*
*  Created on: 2010-1-6
*      Author: zhaoqi
*/

#include <string>
#include "DataManager.h"
#include <opencv/highgui.h>
#include "TexturePatchGS.h"
#include "LaplacianOptimization.h"
#include "RetinexIntrinsic.h"
#include "PMVSPatch.h"
//#include "PerformanceEval.h";
#include "IntrinsicMG.h"


float parzenVariance;

float getGaussianWeight(int distance_to_center)
{
	float param = parzenVariance;
	float result = exp(-distance_to_center*distance_to_center/(2*param*param));
	result = result/(param*sqrt(2*3.14159265));

	return result;
}

// A function to draw the histogram
IplImage* DrawHistogram(CvHistogram *hist, float scaleX=1, float scaleY=1)
{
	// Find the maximum value of the histogram to scale
	// other values accordingly
	float histMax = 0;
	cvGetMinMaxHistValue(hist, 0, &histMax, 0, 0);

	// Create a new blank image based on scaleX and scaleY
	IplImage* imgHist = cvCreateImage(cvSize(256*scaleX, 64*scaleY), 8 ,1);
	cvZero(imgHist);

	// Go through each bin
	for(int i=0;i<255;i++)
	{
		float histValue = cvQueryHistValue_1D(hist, i);		// Get value for the current bin...
		float nextValue = cvQueryHistValue_1D(hist, i+1);	// ... and the next bin

		// Calculate the four points of the polygon that these two
		// bins enclose
		CvPoint pt1 = cvPoint(i*scaleX, 64*scaleY);
		CvPoint pt2 = cvPoint(i*scaleX+scaleX, 64*scaleY);
		CvPoint pt3 = cvPoint(i*scaleX+scaleX, (64-nextValue*64/histMax)*scaleY);
		CvPoint pt4 = cvPoint(i*scaleX, (64-histValue*64/histMax)*scaleY);

		// A close convex polygon
		int numPts = 5;
		CvPoint pts[] = {pt1, pt2, pt3, pt4, pt1};

		// Draw it to the image
		cvFillConvexPoly(imgHist, pts, numPts, cvScalar(255));
	}

	// Return it... make sure you delete it once you're done!
	return imgHist;
}


void testSylvainExample(){
	std::string basePath = "G:/exp_data/intrinsic2/Stroke";
	std::string objName = "box";
	std::string imgPath = basePath + "/" + objName + "/" + "orig.png";
	std::string albedoConsPath = basePath + "/" + objName + "/" + "scribbleSimAlbedo.png";
	std::string shadeConsPath = basePath + "/" + objName + "/" + "scribbleSimShading.png";
	std::string absConsPath = basePath + "/" + objName + "/" + "scribbleAbsolute.png";
	mat_3f albedoConsImg = cv::imread(albedoConsPath) / 255.0;
	mat_3f shadeConsImg = cv::imread(shadeConsPath) / 255.0;
	mat_3f absConsImg = cv::imread(absConsPath) / 255.0;
	Constraint albedoCons = loadUserConstraint(albedoConsImg);
	Constraint shadeCons = loadUserConstraint(shadeConsImg);
	Constraint absCons = loadUserConstraint(absConsImg);
	mat_3f inputImg = cv::imread(imgPath);
	inputImg /= 255.0;
	cv::imshow("img",inputImg);
	cv::waitKey(0);

	//std::string basePath, imgName, imgExt;
	//Utility::pathDecompose(imgPath,basePath,imgName,imgExt);
	char buffer[256];
	float chromTrd = IMConfig::chromThrd;
	float txVar = IMConfig::txVar;
	float txDistThrd = IMConfig::distThrd;
	IMConfig::chromThrd = 0.00015;
	RetinexIntrinsic ri(inputImg);
	ri.init();
	ri.addShadeScrib(shadeCons);
	ri.addAlbedoScrib(albedoCons);
	ri.addAbsShadeScrib(absCons);
	//ri.addAbsShadeScrib(ri.genAbsShadeCons());
	ri.solve();
	ri.decompose(true,true,false,false);
	ri.saveResult(basePath + "/" + objName,objName);
}

void testRetinexIntrinsic(){
	//
	//std::string imgPath = "G:/exp_data/intrinsic2/Texture/moscow/orig.png";
	//std::string imgPath = "C:/Users/manazhao/Downloads/dog.png";
	//std::string imgPath = "G:/exp_data/Steve_Example/dog.png";
	//std::string imgPath = "G:/exp_data/intrinsic2/Texture/box/box_500.png";
	//std::string imgPath = "G:/exp_data/intrinsic2/Texture/blanket/blank.jpg";
	std::string imgPath = "G:/exp_data/intrinsic2/Texture/yarn/orig.bmp";
	mat_3f img1 = cv::imread(imgPath);
	img1 /= 255.0;
	float scale = 1.0;
	mat_3f img;
	cv::resize(img1,img,cv::Size(),scale,scale,cv::INTER_LINEAR);
	cv::imshow("img",img);
	cv::waitKey(0);

	std::string basePath, imgName, imgExt;
	Utility::pathDecompose(imgPath,basePath,imgName,imgExt);
	char buffer[256];
	float chromTrd = IMConfig::chromThrd;
	float txVar = IMConfig::txVar;
	float txDistThrd = IMConfig::distThrd;

	RetinexIntrinsic ri(img);
	Constraint albedoCons = ri.genConsAlbedoCons(IMConfig::distThrd,IMConfig::txVar);
	Constraint absCons = ri.genAbsShadeCons(1.0);
	ri.init();
	//ri.addAlbedoScrib(albedoCons);
	ri.addAbsShadeScrib(absCons);
	ri.solve();
	ri.decompose(true,true,false,false);
	cv::imshow("sd",ri.getDM().getShading());
	cv::imshow("ref",ri.getDM().getAlbedo());
	cv::waitKey(0);
	ri.saveResult(basePath,imgName);
}


void mitEval(){
	//std::string expCfgFile = "G:/exp_data/intrinsic2/MIT/data/exp_config.txt";
	//PerformanceEvaluator pe(expCfgFile);
	//pe.evaluate("RI");
	//pe.testThrd();
	std::cout << "mitEval: removed" << std::endl;
}

void printConsoleUsage(){
	std::cout << "intrinsic -i [input image path] -o [output path, the same to the input by default] -c [chrom threshold, 0.001 by default] -td [texture patch distance, 0.001 by default] \
				 -tv [texture patch variance, 0.05 by default] [-nt] [-gamma]" << std::endl;
}
int consoleUsage(int argc, char** argv){
	bool useTx = true;
	bool gamma = false;
	//std::string imgPath = "G:/exp_data/example_usage/box.png";
	std::string imgPath;
	std::string resultPath;
	double chromTrd = 0.001;
	double txDist = 0.001;
	double txVar = 0.05;

	for(int i = 1; i < argc; i++){
		if(strcmp(argv[i],"-i") == 0)
		{
			imgPath = argv[++i];
			continue;
		}
		if(strcmp(argv[i],"-o") == 0){
			resultPath =  argv[++i];
			continue;
		}
		if(strcmp(argv[i],"-c") == 0){
			chromTrd = atof(argv[++i]);
			continue;
		}
		if(strcmp(argv[i],"-td") == 0){
			txDist = atof(argv[++i]);
			continue;
		}
		if(strcmp(argv[i],"-tv") == 0){
			txVar = atof(argv[++i]);
		}
		if(strcmp(argv[i],"-nt") == 0){
			useTx = false;
		}
		if(strcmp(argv[i],"-gamma") == 0){
			gamma = true;
		}
	}
	if(imgPath == ""){
		std::cout << "invalid input, please follow the usage instruction\n" << std::endl;
		printConsoleUsage();
		return -1;
	}
	if(!bfs::exists(imgPath)){
		std::cout << "the input image file does not exist, please check" << std::endl;
		return -1;
	}
	std::string basePath, imgName, imgExt;
	Utility::replaceCharRep(imgPath,'\\','/');
	Utility::pathDecompose(imgPath,basePath,imgName,imgExt);

	if(resultPath == ""){
		resultPath = basePath;
	}

	if(!bfs::exists(resultPath)){
		std::cout << "output path does not exist, please check" << std::endl;
		return -1;
	}
	char lastChar = resultPath[resultPath.length() - 1];
	if( lastChar == '/' || lastChar == '\\'){
		resultPath = resultPath.substr(0,resultPath.length()-1);
	}
	///print the paramters
	std::cout << "++++++++++ running profile+++++++++++++++++" << std::endl;
	std::cout << "input path:" << imgPath << std::endl;
	std::cout << "output path:" << resultPath << std::endl;
	std::cout << "chromacity threshold:" << chromTrd << std::endl;
	std::cout << "texture distance: " << txDist << std::endl;
	std::cout << "texture variance: " << txVar << std::endl;
	std::cout << "Use texture grouping: " << useTx << std::endl;
	std::cout << "+++++++++++++++++++++++++++++++++++++++++++" << std::endl;
	mat_3f img = cv::imread(imgPath) / 255.0;

	if (gamma) {
		std::cout << "gamma correct (2.2)" << std::endl;
		cv::pow(img,2.2,img);
	}

	std::cout << "width: " << img.size().width << std::endl;
	std::cout << "height: " << img.size().height << std::endl;

	RetinexIntrinsic ri(img);
	IMConfig::txVar = txVar;
	IMConfig::distThrd = txDist;
	IMConfig::chromThrd = chromTrd;
	if(useTx){
		Constraint albedoCons = ri.genConsAlbedoCons(IMConfig::distThrd,IMConfig::txVar);
		ri.addAlbedoScrib(albedoCons);
	}
	Constraint absCons = ri.genAbsShadeCons(1.0);
	ri.addAbsShadeScrib(absCons);
	ri.init();
	ri.solve();
	ri.decompose(true,true,false,gamma);
	ri.saveResult(resultPath,imgName);
	//cv::imshow("input image",img);
	//cv::imshow("shading image",ri.getDM().getShading());
	//cv::imshow("reflectance image",ri.getDM().getAlbedo());
	//cv::waitKey(0);
	std::cout << "success" << std::endl;
	return 0;
}
int main(int argc, char** argv) {
	//testRetinexIntrinsic();
	//testSylvainExample();
	//mitEval();
	return consoleUsage(argc,argv);
}

