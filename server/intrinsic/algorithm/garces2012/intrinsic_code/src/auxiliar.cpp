//----------------------------------------------------------------------
//	File:			auxiliar.cpp
//	Author:			Elena Garces
//	Last modified:	18/07/2012
//	Description:	auxiliar functions
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
//    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
////----------------------------------------------------------------------

#include "auxiliar.h"

//----------------------------------------------------------------------
//	getArgs - get command line arguments
//----------------------------------------------------------------------
gral_params getArgs(int argc, char **argv)
{
	static ifstream dataStream;					// data file stream
	static ifstream queryStream;				// query file stream

	string name_seg_file;
	gral_params parameters;

	parameters.useRsimPairs = true;
	parameters.system_definition = true;
	parameters.gammaCorrect=true;



	if (argc <= 1) {							// no arguments
		cerr << "Incorrect arguments, check README file";
		exit(0);
	}
	int i = 1;
	while (i < argc)	// read arguments
	{
		if (!strcmp(argv[i], "-i")) 													// -i image input
		{
			parameters.name_input.assign(argv[i+1]);

			if (!FileExists(parameters.name_input.c_str()))
			{
				cerr << "Unrecognized file." << parameters.name_input.c_str()<< endl;
				exit(1);
			}
			i++;
		}
		else if (!strcmp(argv[i], "-m")) {		// -m image mask


			if (!FileExists(argv[i+1]))
			{
				cerr << "The mask file is incorrect. Executing without mask\n" ; i++;
			}
			else parameters.name_mask.assign(argv[++i]);
		}

		else if (!strcmp(argv[i], "-only-seg"))				parameters.system_definition = false;
		else if (!strcmp(argv[i], "-no-useRsim"))			parameters.useRsimPairs = false;
		else if (!strcmp(argv[i], "-no-gamma")) 			parameters.gammaCorrect = false;

		i++;
	}

	return parameters;
}


bool FileExists(const char* strFilename) {
  struct stat stFileInfo;
  bool blnReturn;
  int intStat;

  // Attempt to get the file attributes
  intStat = stat(strFilename,&stFileInfo);
  if(intStat == 0) {
    // We were able to get the file attributes
    // so the file obviously exists.
    blnReturn = true;
  } else {
    // We were not able to get the file attributes.
    // This may mean that we don't have permission to
    // access the folder which contains this file. If you
    // need to do that level of checking, lookup the
    // return values of stat which will give you
    // more details on why stat failed.
    blnReturn = false;
  }

  return(blnReturn);
}



string build_name_output(gral_params param, int segMode)
{

	string name_output;

	int found_point=param.name_input.rfind(".");
	if (found_point!=string::npos)
	{
		int found=param.name_input.rfind("/");
		string str2 = param.name_input.substr (found+1,found_point-found-1);
		switch(segMode)
		{
		case KMEANS_SEG:
			{
				name_output.append("./results/Kmeans/"); break;
			}
		case FILE_SEG:
			{
				name_output.append("./results/File/");	break;
			}
		}

		name_output.append(str2);
		if (!param.useRsimPairs) name_output.append("_noRsim");

	}

	return name_output;


}


double computeMean(const CImg<double> &im, const MatteImage& matte, double *variance)
{
	double mean = 0.0;
	int npuntos = 0;

	cimg_forXYC(im, x, y,c)
	{
		if (matte(x,y))
		{	mean+=im(x,y,0,c); npuntos++;}
	}
	mean/=npuntos;

	if (*variance != NULL)
	{
		*variance=0.0;
		cimg_forXYC(im, x, y,c)
		{
			if (matte(x,y))
			{	*variance+=pow(im(x,y,0,c) - mean,2.0); }
		}
		*variance/=npuntos-1;
	}
	return mean;
}


double computeMean(CImg<double> *im, vector<int> listPoints)
{
	double media = 0.0;
	int width = im->width();
	for (unsigned int n = 0; n < listPoints.size(); n++)
	{
		int x = listPoints[n] % width; int y = listPoints[n] / width;
		media += *im->data(x,y,0,0);
	}

	return (media/double(listPoints.size()));
}



est computeMean(CImg<double> *c1, CImg<double> *c2, CImg<double> *c3, vector<int> listPoints)
{
	est values;
	values.a = values.b = values.L = 0.0;

	int width = c1->width();

	for (unsigned int n = 0; n < listPoints.size(); n++)
	{
		int x = listPoints[n] % width; int y = listPoints[n] / width;
		values.L +=  *c1->data(x,y,0,0);
		values.a +=  *c2->data(x,y,0,0);
		values.b +=  *c3->data(x,y,0,0);

	}

	values.L /= listPoints.size();
	values.a /= listPoints.size();
	values.b /= listPoints.size();

	return values;
}

double medianfilter(CImg<double> *original, int x, int y)
{

	int width = original->width();


     //   Pick up window elements
     int k = 0;
     double window[25];

     for (int j = y - 2; j <= y + 2; ++j)
        for (int i = x - 2; i <= x + 2; ++i)

           window[k++] = *original->data(i, j,0,0);


     //   Order elements (only half of them)
     for (int j = 0; j < 13; ++j)
     {
        //   Find position of minimum element
        int min = j;
        for (int l = j + 1; l < 25; ++l)
        if (window[l] < window[min])
           min = l;
        //   Put found minimum element in its place
        const double temp = window[j];
        window[j] = window[min];
        window[min] = temp;
     }

     //   Get result - the middle element

	 return  window[12];

}






int buildGraph(list<edge>& edges,const CImg<double>& image, int max_dist, const MatteImage& matte)
{
	int nvertices = 0;
	cimg_forXY(image,x,y)
		if ( matte(x,y) )
		{
			nvertices++;
			// distance 2
			for (int dist=1; dist <= max_dist; dist++)
			{
				if ( (x < image.width() - dist) && matte(x+dist,y))
					edges.push_back(edge(y*image.width() + x, y*image.width() + (x+dist)));
				if ( (y < image.height() - dist) && matte(x,y+dist) )
					edges.push_back(edge(y*image.width() + x, (y+dist)*image.width() + x));
				if ( (x < image.width() - dist) && (y < image.height() - dist) && matte(x+dist,y+dist) )
					edges.push_back(edge(y*image.width() + x, (y+dist)*image.width() + (x+dist)));
				if ( (x < image.width() - dist) && ((y - dist) >= 0) && matte(x+dist,y-dist) )
					edges.push_back(edge(y*image.width() + x, (y-dist)*image.width() + (x+dist)));
			}

		}

	return nvertices;
}

