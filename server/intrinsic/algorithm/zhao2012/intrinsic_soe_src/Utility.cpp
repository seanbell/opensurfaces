#include "Utility.h"
#include <iostream>
#include <stdio.h>
Utility::Utility() {
}

cv::Mat_<cv::Vec3f> Utility::getChromacityImage(cv::Mat_<cv::Vec3f>& rgbImage) {
	///normalize r,g,b channels
	cv::Size imgSize=rgbImage.size();
	cv::Mat_<float> normImage(imgSize);
	normImage.setTo(cv::Scalar(0, 0, 0));
	cv::Mat_<cv::Vec3f> chromacityImage=rgbImage.clone();
	std::vector<cv::Mat_<float> > rgbPlanes;
	cv::split(rgbImage, rgbPlanes);
	cv::Mat_<float> singlePlane=normImage.clone();
	for (int i=0; i<3; i++) {
		cv::pow(rgbPlanes[i], 2.0, singlePlane);
		cv::add(normImage, singlePlane, normImage);
	}
	cv::sqrt(normImage, normImage);
	for (int i=0; i<3; i++) {
		cv::divide(rgbPlanes[i], normImage, rgbPlanes[i]);
	}
	cv::merge(&rgbPlanes[0], 3, chromacityImage);
	return chromacityImage;
}
float Utility::vecDist(cv::Vec3f& v1, cv::Vec3f& v2) {
	float norm1 = cv::norm(v1);
	float norm2 = cv::norm(v2);

	norm1= (norm1>1e-8 ? 1.0/norm1 : 0);
	norm2= (norm2>1e-8 ? 1.0/norm2 : 0);

	cv::Vec3f v11 = v1;
	cv::Vec3f v22 = v2;
	v11 *= norm1;
	v22 *= norm2;

	return 2 * (1.0 - (v11[0]*v22[0]+v11[1]*v22[1]+v11[2]*v22[2]));
}

float Utility::vecEuDist(cv::Vec3f& v1, cv::Vec3f& v2) {
	float n1 = cv::norm(v1);
	float n2 = cv::norm(v2);
	n1 = n1 < 1e-8 ? 0 : 1/n1;
	n2 = n2 < 1e-8 ? 0 : 1/n2;
	v1 *= n1;
	v2 *= n2;
	float val = cv::norm(v1-v2);
	return val;
	//	std::cout<< val <<std::endl;
}

void Utility::pathDecompose(std::string& input, std::string& path,
		std::string& fileName, std::string& ext) {
	//find the last slash position
	int lastSlashPos = input.find_last_of('/');
	int lastDotPos = input.find_last_of('.');

	path = input.substr(0, lastSlashPos);
	fileName = input.substr(lastSlashPos+1, lastDotPos-lastSlashPos-1);
	ext = input.substr(lastDotPos+1, input.size()-lastSlashPos-1);
}

void Utility::drawField(mat_3f& vecField, mat_3f& canvas, mat_u& mask) {
	cv::Size fieldSize = vecField.size();

	float h, s, v, r1, g, b;
	float avg = 1;
	for (int r=0; r<fieldSize.height; r++) {
		for (int c=0; c<fieldSize.width; c++) {
			if (!mask(r, c))
				continue;
			cv::Vec3f& vec = vecField(r, c);
			float tmpH=vec[0];
			float tmpV=vec[1];
			float orient = 180 * (atan2(tmpV, tmpH)+3.1415926)/3.1415926;
			h = orient;
			s =1;
			v =sqrt(tmpH*tmpH+tmpV*tmpV)/avg;
			Hsv2Rgb(h, s, v, r1, g, b);
			cv::circle(canvas, cv::Point(c, r), 1, cv::Scalar(g, r1, b), 
			CV_FILLED, CV_AA);
		}
	}
}



bool Utility::isSameRef(cv::Vec3f& v1, cv::Vec3f& v2,float nrThrd){
	//first compare the chromacity
	//float n1 = cv::norm(v1);
	//float n2 = cv::norm(v2);
	//if( abs(n1/n2 - 1) < nrThrd && vecDist(v1,v2) < agThrd)
	//	return true;
	//else
	//	return false;
	return cv::norm(v1 - v2) < nrThrd;
}

float Utility::vecAngle(cv::Vec3f& v1, cv::Vec3f& v2) {
	float cosVal = v1.dot(v2);
	return std::acos(cosVal) * 57.29578049;
}

void Utility::Hsv2Rgb(float H, float S, float V, float &R, float &G, float &B) {
	int i;
	float f, p, q, t;

	if (S == 0) {
		// achromatic (grey)
		R = G = B = V;
		return;
	}

	H /= 60; // sector 0 to 5
	i = floor(H);
	f = H - i; // factorial part of h
	p = V * ( 1 - S );
	q = V * ( 1 - S * f );
	t = V * ( 1 - S * ( 1 - f ) );

	switch (i) {
	case 0:
		R = V;
		G = t;
		B = p;
		break;
	case 1:
		R = q;
		G = V;
		B = p;
		break;
	case 2:
		R = p;
		G = V;
		B = t;
		break;
	case 3:
		R = p;
		G = q;
		B = V;
		break;
	case 4:
		R = t;
		G = p;
		B = V;
		break;
	default: // case 5:
		R = V;
		G = p;
		B = q;
		break;
	}
}

void Utility::toEps(std::string imgListFile) {
	FILE* fid = fopen(imgListFile.c_str(), "r");
	char buffer[256];
	std::string base, fileName, fileExt;
	while (fscanf(fid, "%s", buffer)>0) {
		std::string srcFullPath(buffer);
		Utility::pathDecompose(srcFullPath, base, fileName, fileExt);
		std::string dstFullPath = base + "/" + fileName + ".eps";
		//
		std::string cmdStr = "convert " + srcFullPath + " " + dstFullPath;
		std::cout<<cmdStr <<std::endl;
		system(cmdStr.c_str());
	}
	fclose(fid);
}


//void Utility::showFiles( const bfs::path & top, std::vector<std::string>& paths)
//{
	//if (bfs::exists(top))
	//{
		//bfs::directory_iterator end_iter;
		//for (bfs::directory_iterator itr(top); itr != end_iter; ++itr)
		//{
			//if (bfs::is_regular_file(*itr))
			//{
				//paths.push_back(itr->path()->string());
				////std::cout << itr->string() << std::endl;
			//}
		//}
		
	//}
//}

//void Utility::findFilexByExt(std::string topPath1, std::string ext,std::vector<std::string>& filterPaths){
	//bfs::path topPath(topPath1);
	//std::vector<std::string> imageFileList;
	//Utility::showFiles(topPath,imageFileList);
	//for (int i = 0; i < imageFileList.size(); i++)
	//{
		//bfs::path imgFile(imageFileList[i]);
		//if (Utility::filterPath(imageFileList[i],ext))
		//{
			////std::cout << imgFile.string() << std::endl;
			//filterPaths.push_back(imgFile.string());
		//}
	//}
//}

bool Utility::filterPath(std::string input,std::string ext){
	std::transform(ext.begin(),ext.end(),ext.begin(),::tolower);
	bfs::path p(input);
	std::string pExt = p.extension().native();
	std::transform(pExt.begin(),pExt.end(),pExt.begin(),::tolower);
	if (pExt == ext)
	{
		return true;
	}
	

	return false;
	
}

void Utility::replaceCharRep(std::string& str, char target,char replace){
	for(int i = 0; i < str.length(); i++)
	{
		if(str[i] == target){
			str[i] = replace;
		}
	}
}

Utility::~Utility() {
}
