#ifndef UTILITY_H_
#define UTILITY_H_
#include "cv_header.h"
#include "structDef.h"
#include <boost/filesystem.hpp>
#include <boost/foreach.hpp>

namespace bfs = boost::filesystem;

class Utility
{
public:
	Utility();
	static mat_u maskConvert(mat_3f m){
		cv::Size sz = m.size();
		mat_u mask(sz);
		mask = 0;
		for(int i = 0 ; i < sz.height; i++)
			for(int j  = 0; j < sz.width; j++)
				if(cv::norm(m(i,j)))
					mask(i,j) = 255;
		return mask;
	}
	static int pos2index(cv::Point& pt, cv::Size& size){
		return pt.y*size.width+pt.y;
	}
	static cv::Point index2pos(int index,cv::Size& size){
		return cv::Point(index%size.width,index/size.width);
	}
	
	template <class T>
	static void viewImg(std::string winName, T& img){
		cv::namedWindow(winName,CV_WINDOW_AUTOSIZE);
		cv::imshow(winName,img);
		cv::waitKey(0);
	}
	static mat_3f loadImg(std::string path);
	static bool isSameRef(cv::Vec3f& v1, cv::Vec3f& v2,float nrThrd);
	static float vecAngle(cv::Vec3f& v1, cv::Vec3f& v2);
	static void Hsv2Rgb(float H, float S, float V, float &R, float &G, float &B);
	static void drawField(mat_3f& vecField, mat_3f& canvas,mat_u& mask);
	static cv::Mat_<cv::Vec3f> getChromacityImage(cv::Mat_<cv::Vec3f>& rgbImage);
	static float vecDist(cv::Vec3f& v1, cv::Vec3f& v2);
	static float vecEuDist(cv::Vec3f& v1, cv::Vec3f& v2);
	static void pathDecompose(std::string& input, std::string& path, std::string& fileName, std::string& ext);
	static void toEps(std::string imgListFile);
	//static void showFiles( const bfs::path & directory, std::vector<std::string>& path);
	//static void findFilexByExt(std::string topPath, std::string ext,std::vector<std::string>& filterPaths);
	static bool filterPath(std::string input,std::string ext);
	static void replaceCharRep(std::string& input,char target,char replace);
	virtual ~Utility();
};



template< class T>
std::ostream& operator << (std::ostream& oss, const cv::Mat_<T>& mat){
	cv::Size matSize = mat.size();
	for(int i=0;i<matSize.height;i++)
	{
		for(int j=0;j<matSize.width;j++){
			oss << mat(i,j)<<" ";
		}
		oss << std::endl;
	}
	return oss;
}



#endif /*UTILITY_H_*/
