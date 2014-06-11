#include "LaplacianOptimization.h"
#include <cstdio>

grpEle_vect loadUserConstraint(mat_3f strokeImg){
	//each color denotes a stroke
	int iw = strokeImg.size().width;
	int ih = strokeImg.size().height;
	std::vector<cv::Vec3f> strokeColor;
	grpEle_vect strokePixGrp; //
	for (int i = 0; i < ih; i++)
	{
		for (int j = 0; j < iw; j++)
		{
			cv::Vec3f val = strokeImg(i,j);
			if (cv::norm(val) <= 1e-3)
			{
				continue;
			}
			bool exist = false;
			for (int k = 0; k < strokeColor.size() && !exist; k++)
			{
				float dist = cv::norm(val - strokeColor[k]);
				//std::cout << dist << std::endl;
				if (dist <= 1e-3)
				{
					GrpEle& grp = strokePixGrp[k];
					Element ele(i * iw + j,1.0);
					ele.m_rgb = strokeColor[k];
					grp.m_eMember.push_back(ele);
					exist = true;
				}
			}
			if (!exist)
			{

				//add a new group
				strokeColor.push_back(val);
				GrpEle newGrp;
				Element ele(i * iw + j, 1.0);
				ele.m_rgb[0] = val[0];
				ele.m_rgb[1] = val[1];
				ele.m_rgb[2] = val[2];
				newGrp.m_eMember.push_back(ele);
				newGrp.m_gID = strokeColor.size();
				strokePixGrp.push_back(newGrp);

			}
		}
	}
	//verifyUserConstraint(strokeImg,strokePixGrp,strokeColor);
	return strokePixGrp;
}

//void verifyUserConstraint(grpEle_vect& strokes,int h , int w){
	//mat_3f strokeImg(h,w);
	//strokeImg = 0;
	//std::vector<cv::Vec3f> strokeColor(strokes.size());
	//for (int i = 0; i < strokes.size(); i++)
	//{
		//float r = (float)rand()/((float)RAND_MAX + 1);
		//float g = (float)rand()/((float)RAND_MAX + 1);
		//float b = (float)rand()/((float)RAND_MAX + 1);
		//strokeColor[i] = cv::Vec3f(r,g,b);
	//}
	//verifyUserConstraint(strokeImg,strokes,strokeColor);
//}

//void verifyUserConstraint(mat_3f strokeImg, grpEle_vect& strokes, std::vector<cv::Vec3f>& strokeColor){
	////
	//mat_3f canvas = strokeImg.clone();
	//int iw = canvas.size().width;
	//canvas  = cv::Vec3f(0,0,0);
	//for (int i = 0; i < strokes.size(); i++)
	//{
		//GrpEle& grp  = strokes[i];
		//for (int j  = 0; j < grp.m_eMember.size(); j++)
		//{
			//int px = grp.m_eMember[j].m_eleID % iw;
			//int py = grp.m_eMember[j].m_eleID / iw;
			//if(py >= canvas.size().height || px >= canvas.size().width)
			//{
				//std::cout << "out of bound" << std::endl;
				//getchar();
			//}
			//canvas(py,px) = strokeColor[i];
		//}

	//}
	//char buffer[256];
	//sprintf(buffer,"window_%d_%d",iw,canvas.size().height);
	//cv::imshow(buffer,canvas);
	//cv::waitKey(0);

//}

#define __OPENCV_PINV__
mat_f pinv(mat_f input){
	//
	cv::Size inputSize = input.size();
	cv::Size invSize(inputSize.width,inputSize.height);
	mat_f pinvMat(invSize);
	//
#ifdef __OPENCV_PINV__
	cv::invert(input,pinvMat,1);
#else
	Utility::gslPseudoInverse(input,pinvMat);
#endif
	return pinvMat;
}
