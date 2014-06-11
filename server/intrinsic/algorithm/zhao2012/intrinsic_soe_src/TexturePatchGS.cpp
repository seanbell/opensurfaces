#include "TexturePatchGS.h"

TexturePatchGS::TexturePatchGS(DataManager* dmPtr,std::string gsName)
:RefGS(dmPtr,gsName)
{
	m_iWidth = 0;
	m_iHeight = 0;
	m_patchsize = 3;
	m_trd_dist = 0.001; //0.01
	m_trd_max = m_trd_dist * 5;
	m_trd_chrvar = 0.1;//0.05;
	m_trd_noise = 1e-3;
	m_rotation = 4;
	m_IsMultipleMatch = AppConfig::m_multMatch;
	m_IsSoftMatch = AppConfig::m_softMatch;
	m_iternum = AppConfig::m_trw_iterCnt;
	m_smoothS = AppConfig::m_shadingWeight;
	m_smoothR = AppConfig::m_refWeight;

}


void TexturePatchGS::getPatch(mat_3f& input, int l, int t, int patchsize,int rotation,float* data){
	int r,b;

	int m_width = input.size().width;
	int m_height = input.size().height;


	r = std::min(m_width, l + patchsize); //right
	b = std::min(m_height, t + patchsize); //bottom

	switch(rotation)
	{
	case 0:	//0
		for(int i = t; i < b; i++)
			for(int j = l; j < r; j++)
			{
				cv::Vec3f& pix = input(i,j);
				//					float *pos = m_data + (i*m_width + j)*3;
				//					*data++ = *pos++; 
				//					*data++ = *pos++;
				//					*data++ = *pos++;
				*data++ = pix[0];
				*data++ = pix[1];
				*data++ = pix[2];
			}
			break;
	case 1: //90
		for(int i = l; i < r; i++)
			for(int j = b-1; j >= t; j--)
			{
				cv::Vec3f& pix = input(j,i);
				*data++ = pix[0];
				*data++ = pix[1];
				*data++ = pix[2];

				//					float *pos = m_data + (j*m_width + i)*3;
				//					*data++ = *pos++;
				//					*data++ = *pos++;
				//					*data++ = *pos++;
			}
			break;
	case 2: //180
		for(int i = b-1; i >= t; i--)
			for(int j = r-1; j >= l; j--)
			{
				cv::Vec3f& pix = input(i,j);
				*data++ = pix[0];
				*data++ = pix[1];
				*data++ = pix[2];

				//					float *pos = m_data + (i*m_width + j)*3;
				//					*data++ = *pos++;
				//					*data++ = *pos++;
				//					*data++ = *pos++;
			}
			break;
	case 3://270
		for(int i = r-1; i >= l; i--)
			for(int j = t; j < b; j++)
			{
				cv::Vec3f& pix = input(j,i);
				*data++ = pix[0];
				*data++ = pix[1];
				*data++ = pix[2];

				//					float *pos = m_data + (j*m_width + i)*3;
				//					*data++ = *pos++;
				//					*data++ = *pos++;
				//					*data++ = *pos++;
			}
			break;
	}	

}

float TexturePatchGS::computeVar(mat_f& A){
	int h = A.size().height;
	float avg[] = {0,0,0};
	for(int i=0;i<h;i++)
	{
		avg[0] += A(i,0);
		avg[1] += A(i,1);
		avg[2] += A(i,2);
	}
	avg[0] /= h;
	avg[1] /= h;
	avg[2] /= h;
	//
	float var = 0 ;
	for(int i=0;i<h;i++)
	{
		float d1 = avg[0] - A(i,0);
		float d2 = avg[1] - A(i,1);
		float d3 = avg[2] - A(i,2);
		var += (d1*d1+d2*d2+d3*d3);
	}
	var /= h;
	var = sqrt(var);
	return var;
}

void TexturePatchGS::buildTxPool(){
	int nsize = m_iWidth * m_iHeight;

	mat_3f& chromImg = m_dmPtr->getChrom();
	mat_3f& inputImg = m_dmPtr->getInput();

	printf("Collect txtured pixels...\n");

	int nx, ny, offset, halfsize, nn;
	float center[3], noise;
	//	Matrix A;

	nx = m_iWidth - m_patchsize + 1;
	ny = m_iHeight - m_patchsize + 1;
	nn = m_patchsize * m_patchsize;
	halfsize = m_patchsize >> 1;

	mat_f A(nn,3);
	//	A.resize(nn, 3);
	noise = pow(m_trd_noise * 1.0, 2);

	// initialize txpixels
	for(int i = 0 ; i < nsize; i++)
		m_txPixels[i].m_istextured = false;

	m_txPixelId.clear();

	for(int i = 0; i < ny; i++)
		for(int j = 0; j < nx; j++)
		{
			float var;

			getPatch(chromImg,j,i,m_patchsize,0,(float*)A.data);

			//		m_pfmChromImg.GetPatch(j, i, m_pa	tchsize,0, A.Store());

			cv::Vec3f& pixCenter = inputImg(i+halfsize,j+halfsize);
			//		m_pfmInputImg.GetPixelValue(j+halfsize, i+halfsize, center);

			center[0]  = pixCenter[0];
			center[1]  = pixCenter[1];
			center[2]  = pixCenter[2];

			var = center[0]*center[0] + center[1]*center[1] + center[2]*center[2];

			if(var>noise)
			{

				//			var = sqrt(1-A.sum_columns().sum_square()/(nn*nn)); // std = sqrt(1/n sigma(x - avg(x))^2);
				var = computeVar(A);
				if(var > m_trd_chrvar)
				{
					int pos = (i+halfsize)*m_iWidth+j+halfsize; //get the center position
					m_txPixels[pos].m_istextured = true;
					m_txPixelId.push_back(pos);
				}
			}
		}

		nsize = m_txPixelId.size();
		printf("The number of textured pixels: %d\n", nsize);

		// put the texture pixels into m_txChains for showing
		if (nsize>0)
		{
			m_txChains.resize(1);
			m_txChains[0].m_pixelID = m_txPixelId;
			m_txChains[0].m_windowsize.resize(nsize, m_patchsize);
		}
}

void TexturePatchGS::Rotation(ANNpoint queryPt, ANNpoint dataPt, int r, int patchsize)
{
	int dim = patchsize * patchsize * 3;
	switch(r)
	{
	case 0://0
		while(dim--)
			queryPt[dim] = dataPt[dim];
		break;
	case 1://90
		for(int i=0; i<patchsize; i++)
			for(int j=patchsize-1; j>=0; j--)
			{
				ANNpoint data = dataPt + (j*patchsize+i)*3;
				*queryPt++ = *data++;
				*queryPt++ = *data++;
				*queryPt++ = *data++;
			}
			queryPt -= dim;
			break;
	case 2://180
		for(int i=patchsize-1; i>=0; i--)
			for(int j=patchsize-1; j>=0; j--)
			{
				ANNpoint data = dataPt + (i*patchsize+j)*3;
				*queryPt++ = *data++;
				*queryPt++ = *data++;
				*queryPt++ = *data++;
			}
			queryPt -= dim;
			break;
	case 3://270
		for(int i=patchsize-1; i>=0; i--)
			for(int j=0; j<patchsize; j++)
			{
				ANNpoint data = dataPt + (j*patchsize+i)*3;
				*queryPt++ = *data++;
				*queryPt++ = *data++;
				*queryPt++ = *data++;
			}
			queryPt -= dim;
			break;
	}
}


void TexturePatchGS::RotationAdd(ANNpoint queryPt, ANNpoint dataPt, int r, int patchsize)
{
	int dim = patchsize * patchsize * 3;
	switch(r)
	{
	case 0://0
		while(dim--)
			queryPt[dim] += dataPt[dim];
		break;
	case 1://90
		for(int i=0; i<patchsize; i++)
			for(int j=patchsize-1; j>=0; j--)
			{
				ANNpoint data = dataPt + (j*patchsize+i)*3;
				*queryPt++ += *data++;
				*queryPt++ += *data++;
				*queryPt++ += *data++;
			}
			queryPt -= dim;
			break;
	case 2://180
		for(int i=patchsize-1; i>=0; i--)
			for(int j=patchsize-1; j>=0; j--)
			{
				ANNpoint data = dataPt + (i*patchsize+j)*3;
				*queryPt++ += *data++;
				*queryPt++ += *data++;
				*queryPt++ += *data++;
			}
			queryPt -= dim;
			break;
	case 3://270
		for(int i=patchsize-1; i>=0; i--)
			for(int j=0; j<patchsize; j++)
			{
				ANNpoint data = dataPt + (j*patchsize+i)*3;
				*queryPt++ += *data++;
				*queryPt++ += *data++;
				*queryPt++ += *data++;
			}
			queryPt -= dim;
			break;
	}
}

void TexturePatchGS::Cluster(vect_i& pixelId, int patchsize)
{
	//pixelID keeps the patch center positions

	mat_3f& chromImg = m_dmPtr->getChrom();

	int nPts, *pId, dim, n, chain_num;
	float *data, val[3], trd_dist;
	ANNpointArray dataPts; // data points
	vec pixelgroups;

	nPts = pixelId.size();

	pId = &pixelId[0];
	dataPts = annAllocPts(nPts, 3); //just patch center pixel positions??? not patch?

	for(int i=0; i<nPts; i++)
	{
		cv::Vec3f cVal = chromImg(pId[i]/m_iWidth,pId[i]%m_iWidth);
		//		m_pfmChromImg.GetPixelValue(pId[i], 0, val);
		val[0] = cVal[0];
		val[1] = cVal[1];
		val[2] = cVal[2];
		dataPts[i][0] = val[0];
		dataPts[i][1] = val[1];
		dataPts[i][2] = val[2];
	}
#ifdef __AVG_PATCH__
	TextureMatch(dataPts, 1, pixelId, pixelgroups);
#else
	TextureMatch2(dataPts, 1, pixelId, pixelgroups);
#endif

	n = pixelgroups.size();
	dim = patchsize * patchsize * 3;
	data = new float[dim];
	chain_num = 0;
	m_txChains.clear();

	int halfsize = m_patchsize >> 1; //
	for(int i=0; i<n; i++)
	{
		nPts = pixelgroups[i].m_pixelID.size();
		pId = & pixelgroups[i].m_pixelID[0];
		dataPts = annAllocPts(nPts, dim);

		for(int k=0; k<nPts; k++)
		{
			ANNpoint queryPt = dataPts[k];
#ifdef __MODIFY__
			getPatch(chromImg,pId[k]%m_iWidth - halfsize, pId[k]/m_iWidth - halfsize, patchsize, 0, data); /// 
#else
			getPatch(chromImg,pId[k]%m_iWidth, pId[k]/m_iWidth, patchsize, 0, data); ///center position, not the left top 
#endif
			//			m_pfmChromImg.GetPatch(pId[k]%m_iWidth, pId[k]/m_iWidth, patchsize, 0, data);

			for(int j=0; j<dim; j++)
				*queryPt++ = data[j];
		}
#ifdef __AVG_PATCH__
		TextureMatch(dataPts, patchsize, pixelgroups[i].m_pixelID, m_txChains);
#else
		TextureMatch2(dataPts, patchsize, pixelgroups[i].m_pixelID, m_txChains);
#endif
	}

	delete [] data;
}

void TexturePatchGS::DestryKdTree(ANNkd_tree * tree)
{
	if(tree != NULL){
		ANNpointArray pts = tree->thePoints();
		annDeallocPts(pts);
		delete tree;
		annClose();
	}
}


void TexturePatchGS::TextureMatch2(ANNpointArray dataPts, int patchsize, vect_i& pixelId,vec& groups){
	mat_3f& chromImg = m_dmPtr->getChrom();
	ANNpoint queryPt, avgPt; // query point
	ANNidxArray nnIdx; // near neighbor indices
	ANNdistArray dists; // near neighbor distances
	ANNkd_tree* txTree;
	int dim, nPts, *pId, *f, nn;
	float trd_dist, *info;
	char r;
	vect_i flag;

	nn = patchsize * patchsize;
	dim = nn * 3;

	nPts = pixelId.size();

	pId = &pixelId[0];

	txTree = new ANNkd_tree(dataPts, nPts, dim);
	nnIdx = new ANNidx[nPts]; // allocate near neigh indices
	dists = new ANNdist[nPts]; // allocate near neighbor dists
	queryPt = annAllocPt(dim); // allocate query point
	avgPt = annAllocPt(dim);

	trd_dist = m_trd_dist * nn;
	r = patchsize==1? 1: m_rotation;

	flag.resize(nPts, -1);
	f = &flag[0];
	for(int i=0; i<nPts; i++)
	{

		if (f[i] >= 0)
			continue;

		SuperPixel Sp;

		vect_f pinfo(nPts, trd_dist);
		float *info = &pinfo[0], nor;

		
		for(int j=0; j<r; j++)
		{
			Rotation(queryPt, dataPts[i], j, patchsize); 
			int n = txTree->annkFRSearch(queryPt, trd_dist, nPts,nnIdx, dists);

			if (n > 1)
			{

				for(int k=0; k<n; k++)
				{
					int pos = nnIdx[k];

					if(info[pos]> dists[k])
					{
						info[pos] = dists[k]; //keep the minimum distance match(since the query patch do the match after 90 degrees rotation each time)
						f[pos] = j;  //keep the rotation,
					}
				}
			}
		}

		float chrom[] = {0,0,0}, val[3];

		for(int k=0; k<nPts; k++)
		{
			if(info[k]<trd_dist) //a match detected(why not use the rotation array directly, if( f[k] < 0)....
			{
				int pos = pId[k];

				cv::Vec3f cVal = chromImg(pos/m_iWidth,pos%m_iWidth);
				val[0] = cVal[0];
				val[1] = cVal[1];
				val[2] = cVal[2];
				//						m_pfmChromImg.GetPixelValue(pos, 0, val);

				chrom[0] += val[0];
				chrom[1] += val[1];
				chrom[2] += val[2];

				Sp.m_pixelID.push_back(pos); //pixel index
				Sp.m_rotation.push_back(f[k]); //rotation index
				Sp.m_confidence.push_back(1.0 - info[k]/trd_dist); //membership confidence
			}
		}
		if (Sp.m_pixelID.size() > 1)
		{

			Sp.m_windowsize.resize(Sp.m_pixelID.size(), patchsize);

			nor = sqrt(chrom[0]*chrom[0] + chrom[1]*chrom[1] + chrom[2]*chrom[2]);
			nor = nor<1e-8? 0: 1.0/nor;
			Sp.m_chrom[0] = chrom[0]*nor;
			Sp.m_chrom[1] = chrom[1]*nor;
			Sp.m_chrom[2] = chrom[2]*nor;
			Sp.m_shading = 0;
			groups.push_back(Sp);
		}
	}

	delete [] nnIdx;
	delete [] dists;

	annDeallocPt(queryPt);
	annDeallocPt(avgPt);
	DestryKdTree(txTree);
}

void TexturePatchGS::TextureMatch(ANNpointArray dataPts, int patchsize,vect_i& pixelId, vec& groups)
{
	mat_3f& chromImg = m_dmPtr->getChrom();
	ANNpoint queryPt, avgPt; // query point
	ANNidxArray nnIdx; // near neighbor indices
	ANNdistArray dists; // near neighbor distances
	ANNkd_tree* txTree;
	int dim, nPts, *pId, *f, nn;
	float trd_dist, *info;
	char r;
	vect_i flag;

	nn = patchsize * patchsize;
	dim = nn * 3;

	nPts = pixelId.size();

	pId = &pixelId[0];

	txTree = new ANNkd_tree(dataPts, nPts, dim);
	nnIdx = new ANNidx[nPts]; // allocate near neigh indices
	dists = new ANNdist[nPts]; // allocate near neighbor dists
	queryPt = annAllocPt(dim); // allocate query point
	avgPt = annAllocPt(dim);

	trd_dist = m_trd_dist * nn;
	r = patchsize==1? 1: m_rotation;

	flag.resize(nPts, -1);
	f = &flag[0];
	for(int i=0; i<nPts; i++)
	{
		if(f[i]<0) //current patch is unmatched
		{
			SuperPixel Sp;
			int num(0);

			for(int j=0; j<dim; j++) avgPt[j] = 0;

			for(int j=0; j< r; j++)
			{
				Rotation(queryPt, dataPts[i], j, patchsize);

				int n = txTree->annkFRSearch(queryPt, trd_dist, nPts,nnIdx, dists);

				if(n>1)
				{
					for(int k=1; k<n; k++)
					{
						int pos = nnIdx[k]; //matched patch index

						for(int l=0; l<dim; l++)
							queryPt[l] += dataPts[pos][l]; //add up all the matched patches
					}
					num += n;
					RotationAdd(avgPt, queryPt, (4-j)%4, patchsize); //rotate the summed patches to the same orientation and add them to the preveously matched patches
				}
			}

			if(num>0)
			{
				vect_f pinfo(nPts, trd_dist);
				float *info = &pinfo[0], nor;

				for(int k=0; k<nn; k++)
				{
					float nor = sqrt(avgPt[0] * avgPt[0] + avgPt[1] * avgPt[1] + avgPt[2] * avgPt[2]);
					nor = nor<1e-8? 0: 1.0/nor;
					*avgPt++ *= nor;
					*avgPt++ *= nor;
					*avgPt++ *= nor; //each pixel of the patch should be normalized(chromacity)
				}
				avgPt -= dim;

				for(int j=0; j<r; j++)
				{
					Rotation(queryPt, avgPt, j, patchsize); //query again with the average patch

					int n = txTree->annkFRSearch(queryPt, trd_dist, nPts,nnIdx, dists);

					for(int k=0; k<n; k++)
					{
						int pos = nnIdx[k];

						if(info[pos]> dists[k])
						{
							info[pos] = dists[k]; //keep the minimum distance match(since the query patch do the match after 90 degrees rotation each time)
							f[pos] = j;  //keep the rotation
						}
					}
				}

				float chrom[] = {0,0,0}, val[3];

				for(int k=0; k<nPts; k++)
				{
					if(info[k]<trd_dist) //a match detected(why not use the rotation array directly, if( f[k] < 0)....
					{
						int pos = pId[k];

						cv::Vec3f cVal = chromImg(pos/m_iWidth,pos%m_iWidth);
						val[0] = cVal[0];
						val[1] = cVal[1];
						val[2] = cVal[2];
						//						m_pfmChromImg.GetPixelValue(pos, 0, val);

						chrom[0] += val[0];
						chrom[1] += val[1];
						chrom[2] += val[2];

						Sp.m_pixelID.push_back(pos); //pixel index
						Sp.m_rotation.push_back(f[k]); //rotation index
						Sp.m_confidence.push_back(1.0 - info[k]/trd_dist); //membership confidence
					}
				}
				Sp.m_windowsize.resize(Sp.m_pixelID.size(), patchsize);

				nor = sqrt(chrom[0]*chrom[0] + chrom[1]*chrom[1] + chrom[2]*chrom[2]);
				nor = nor<1e-8? 0: 1.0/nor;
				Sp.m_chrom[0] = chrom[0]*nor;
				Sp.m_chrom[1] = chrom[1]*nor;
				Sp.m_chrom[2] = chrom[2]*nor;
				Sp.m_shading = 0;

				groups.push_back(Sp);
			}
		}
	}

	delete [] nnIdx;
	delete [] dists;

	annDeallocPt(queryPt);
	annDeallocPt(avgPt);
	DestryKdTree(txTree);
}

void TexturePatchGS::CheckLargerWindow(int windowsize)
{

	mat_3f& chromImg =m_dmPtr->getChrom();
	int dim, nPts, *pId, nchain, nn;
	float trd_dist, *data, *mean;

	nn = windowsize * windowsize;
	dim = nn * 3;
	mean = new float[dim];
	trd_dist = nn * m_trd_dist;
	nchain = m_txChains.size();

	int halfsize = m_patchsize >> 1;
	for(int i=0; i<nchain; i++)
	{
		int *r;

		nPts = m_txChains[i].m_pixelID.size();

		if(nPts>1)
		{
			r = &m_txChains[i].m_rotation[0];
			pId = &m_txChains[i].m_pixelID[0];
			data = new float[dim*nPts];

			for(int k=0; k<dim; k++) mean[k] = 0;

			for(int k=0; k<nPts; k++)
			{
				int pos = pId[k];
#ifdef __MODIFY__
				getPatch(chromImg,pos%m_iWidth - halfsize, pos/m_iWidth - halfsize, windowsize,(4 - r[k]) % 4, data); //rotate it back??? something must be wrong here...., shouldn't the rotation be (4 - r[k]) % 4
#else
				getPatch(chromImg,pos%m_iWidth, pos/m_iWidth, windowsize, r[k], data); //rotate it back??? something must be wrong here...., shouldn't the rotation be (4 - r[k]) % 4

#endif
				//				m_pfmChromImg.GetPatch(pos%m_iWidth, pos/m_iWidth, windowsize, r[k], data);

				for(int j=0; j<dim; j++)
					mean[j] += data[j];

				data += dim;
			}
			for(int k=0; k<nn; k++)
			{
				float nor;
				nor = sqrt(mean[0]*mean[0] + mean[1]*mean[1] + mean[2]*mean[2]);
				nor = nor<1e-8? 0: 1.0/nor;
				*mean++ *= nor;
				*mean++ *= nor;
				*mean++ *= nor;
			}
			mean -= dim;

			while(nPts--)
			{
				int j(dim);
				float dist(0);

				while(j--)
					dist += pow(*--data - mean[j],2);

				if( dist<trd_dist)
					m_txChains[i].m_windowsize[nPts] = windowsize;
			}
			delete [] data;
		}
	}
	delete [] mean;
}

mat_3f TexturePatchGS::CreateMozacCanvas(int hMaxCnt, int vMaxCnt, int patchSize, int sep){
	int w = hMaxCnt * (patchSize + sep);
	int h = vMaxCnt * (patchSize + sep);
	mat_3f canvas(h,w);
	canvas = cv::Vec3f(0,0,0);
	return canvas;
}


void TexturePatchGS::MozacPatch(mat_3f& canvas, mat_3f& patch, int patSep, int patchId){

	int patchSize = patch.size().width;
	int hCnt = canvas.size().width / (patchSize + patSep);
	int vCnt = canvas.size().height / (patchSize + patSep);

	int ix = patchId % hCnt;
	int iy = patchId / hCnt;
	int px = ix * (patchSize + patSep);
	int py = iy * (patchSize + patSep);

	for (int i = 0; i < patchSize; i++)
	{
		for (int j = 0; j < patchSize; j++)
		{
			canvas(py + i, px + j) = patch(i,j); //setting patch
		}

	}

}


void TexturePatchGS::PatchRotation(mat_3f& input, mat_3f& output, int r){


	int patchsize = input.size().width;

	switch(r)
	{
	case 0://0
		output = input; 
		break;
	case 1://90
		for(int i=0 ,i1 = 0; i<patchsize&&i1 <patchsize; i++,i1++)
			for(int j=patchsize-1,j1 =0; j>=0 && j1 <patchsize; j--,j1++)
			{
				output(i1,j1) = input(j,i);
				//float* data = inputData + ( j * patchsize+i)*3;
				//*outputData++ = *data++;
				//*outputData++ = *data++;
				//*outputData++ = *data++;
			}
			break;
	case 2://180
		for(int i=patchsize-1,i1 = 0; i>=0 && i1 < patchsize; i--,i1++)
			for(int j=patchsize-1,j1=0; j>=0 && j1 <patchsize; j--,j1++)
			{
				output(i1,j1) = input(i,j);
				/*			float* data = inputData + ( i * patchsize + j)*3;
				*outputData++ = *inputData++;
				*outputData++ = *inputData++;
				*outputData++ = *inputData++;*/

				//ANNpoint data = dataPt + (i*patchsize+j)*3;
				//*queryPt++ = *data++;
				//*queryPt++ = *data++;
				//*queryPt++ = *data++;
			}
			//queryPt -= dim;
			break;
	case 3://270
		for(int i = patchsize-1,i1 = 0; i >= 0 && i1 <patchsize; i--,i1++)
			for(int j=0,j1 = 0; j<patchsize&& j1 <patchsize; j++,j1++)
			{
				output(i1,j1) = input(j,i);
				//float* data = inputData + ( j * patchsize + i)*3;
				//*outputData++ = *inputData++;
				//*outputData++ = *inputData++;
				//*outputData++ = *inputData++;

				//ANNpoint data = dataPt + (j*patchsize+i)*3;
				//*queryPt++ = *data++;
				//*queryPt++ = *data++;
				//*queryPt++ = *data++;
			}
			//queryPt -= dim;
			break;
	}
}


#define __CANVAS__


bool ChainSizeGreat(const SuperPixel& sp1, const SuperPixel& sp2){
	return sp1.m_pixelID.size() > sp2.m_pixelID.size();
}

bool GrpSizeGreat(const GrpEle& ge1, const GrpEle& ge2){

	return ge1.m_eMember.size() > ge2.m_eMember.size();

}


//#define __NO_ROT__ //no rotation applied
template <class T>
class SortPos{
public:
	int m_idx;
	T m_val;
	SortPos(int idx, T val)
		:m_idx(idx),m_val(val){}
};

template<class T> 
bool SortPosGreater(const SortPos<T>& sp1,const SortPos<T>& sp2){
	return sp1.m_val > sp2.m_val;
}

void GrpSortByConf(SuperPixel& sp){
	SuperPixel sp1 = sp;
	std::vector<SortPos<float> > vec1;
	for (int i = 0; i < sp1.m_pixelID.size(); i++)
	{
		vec1.push_back(SortPos<float>(i,sp1.m_confidence[i]));
	}
	std::sort(vec1.begin(),vec1.end(),SortPosGreater<float> );
	for (int i = 0; i < sp1.m_pixelID.size(); i++)
	{
		SortPos<float>& idx = vec1[i];
		sp.m_pixelID[i] = sp1.m_pixelID[idx.m_idx];
		sp.m_confidence[i] = sp1.m_confidence[idx.m_idx];
		sp.m_rotation[i] = sp1.m_rotation[idx.m_idx];
		sp.m_windowsize[i] = sp1.m_windowsize[idx.m_idx];
	}
	
}

float PatchSSD(const mat_3f& v1,const mat_3f& v2){
	float sum = 0;
	for (int i = 0; i < v1.size().height; i++)
	{
		for (int j = 0; j < v1.size().width; j++)
		{
			float tmp = cv::norm(v1(i,j) - v2(i,j));
			sum += (tmp*tmp);
		}
		
	}
	return sum;
}
float PatchMaxDist(const mat_3f& v1, const mat_3f& v2){
	float dist = 0;
	for (int i = 0; i < v1.size().height; i++)
	{
		for (int j = 0; j < v1.size().width; j++)
		{
			float td = cv::norm(v1(i,j) - v2(i,j));
			td = td * td;
			if (td > dist)
			{
				dist = td;
			}
			
		}
	}
	return dist;
}

void TexturePatchGS::RefineGrp(SuperPixel& sp){
	//
	mat_3f& input = m_dmPtr->getInput();
	mat_3f& chrom  = m_dmPtr->getChrom();
	int iw = input.size().width;
	int halfsize = m_patchsize >> 1;
	mat_3f refPatch(m_patchsize,m_patchsize);
	mat_3f refRot = refPatch.clone();
	mat_3f curPatch = refPatch.clone();
	mat_3f curRot = curPatch.clone();

	FetchPatch(chrom,sp.m_pixelID[0]/iw - halfsize, sp.m_pixelID[0]%iw - halfsize,refPatch);
	PatchRotation(refPatch,refRot,(4 - sp.m_rotation[0])%4);
	SuperPixel refinedSp = sp;
	refinedSp.m_confidence.clear();
	refinedSp.m_pixelID.clear();
	refinedSp.m_rotation.clear();
	refinedSp.m_windowsize.clear();

	
	for (int i = 0 ; i < sp.m_pixelID.size(); i++)
	{
		FetchPatch(chrom,sp.m_pixelID[i]/iw - halfsize, sp.m_pixelID[i]%iw - halfsize,curPatch);
		PatchRotation(curPatch,curRot,(4 - sp.m_rotation[i]) % 4);
		float ssd  = PatchSSD(refRot,curRot);
		float dist = PatchMaxDist(refRot,curRot);
		if (dist < m_trd_max)
		{
			refinedSp.m_pixelID.push_back(sp.m_pixelID[i]);
			refinedSp.m_confidence.push_back(sp.m_confidence[i]);
			refinedSp.m_windowsize.push_back(sp.m_windowsize[i]);
			refinedSp.m_rotation.push_back(sp.m_rotation[i]);
		}
	}
	sp = refinedSp;
}

void TexturePatchGS::GrpMozac(std::string basePath){

	int totalPatchCnt = 0;
	int maxSize = -1;
	vec grpBk = m_txChains;
	//
	std::sort(grpBk.begin(),grpBk.end(),ChainSizeGreat); //
	for (int i = 0; i < grpBk.size(); i++)
	{
		SuperPixel& grp = grpBk[i];
		GrpSortByConf(grp);
	}
	std::sort(grpBk.begin(),grpBk.end(),ChainSizeGreat); //
	std::vector<float> maxConfVec;

	for (int i = 0; i < grpBk.size(); i++)
	{
		SuperPixel& sp = grpBk[i];

		int pixCnt = sp.m_pixelID.size();

		if ( pixCnt > maxSize)
		{
			maxSize = sp.m_pixelID.size();
		}
		//
		float maxConf = 0;
		for (int j = 0; j < sp.m_pixelID.size(); j++)
		{
			float conf = sp.m_windowsize[j] * sp.m_confidence[j];
			if (conf > maxConf)
			{
				maxConf = conf;
			}

		}
		maxConfVec.push_back(maxConf);
		//
		totalPatchCnt += sp.m_pixelID.size(); //get # of elements in this group
	}
	//# of patches per canvas
	int sep = 1;
	int pSize = sep + m_patchsize; //
	int hCnt = maxSize * 2 + 2;
	int vCnt = 20;

	int hSize = (sep + m_patchsize) * hCnt;
	int vSize = (sep + m_patchsize) * vCnt * 3; // rgb,chromacity, confidence
	int beginPatchIndex = 0;

	mat_3f canvas(vSize,hSize); //create the canvas
	canvas = cv::Vec3f(0,0,0); //black ground
	int canvasCnt = 0;
	char buffer[256];

	int iW = m_dmPtr->getImgSize().width;

	mat_3f patch = mat_3f(m_patchsize,m_patchsize);
	mat_3f rotPatch = patch.clone();
	int halfsize = m_patchsize >> 1;

	for (int i = 0; i < grpBk.size(); i++)
	{
		SuperPixel& grp = grpBk[i];
		int grpSize = grp.m_pixelID.size();
		//

		int pindx = beginPatchIndex % hCnt;
		int pindy = beginPatchIndex / hCnt;

		int tmpR = hCnt - pindx;

		if ( tmpR < grpSize)
		{

			pindx = 0;
			pindy ++;
			beginPatchIndex += tmpR; //

		}

		if( (beginPatchIndex + grpSize > hCnt * vCnt) || (i == grpBk.size() - 1)){
			//save current group
			sprintf(buffer,"%s/tpgs_%06d.png",basePath.c_str(),canvasCnt++);
			cv::imwrite(std::string(buffer),canvas * 255.0); //
			canvas  = cv::Vec3f(0,0,0);
			beginPatchIndex = 0; //reset
			pindx = pindy = 0;
		}

		if(grpSize == 1)
			continue;

		for (int j = 0; j < grp.m_pixelID.size(); j++)
		{
			int pixID = grp.m_pixelID[j];
			int rot = ( 4 - grp.m_rotation[j]) % 4;
			int px = pixID % iW;
			int py = pixID / iW;

			int rgbPIdx = (pindy * 3 * hCnt) + pindx;
			int chromPIdx = rgbPIdx + hCnt;
			int confPIdx = chromPIdx + hCnt;

			FetchPatch(m_dmPtr->getInput(),py - halfsize, px - halfsize,patch);
			PatchRotation(patch,rotPatch,rot);
			MozacPatch(canvas,rotPatch,sep,rgbPIdx); //rgb patch

			FetchPatch(m_dmPtr->getChrom(),py - halfsize, px - halfsize,patch);
			PatchRotation(patch,rotPatch,rot);
			MozacPatch(canvas,rotPatch,sep,chromPIdx); //next cnt

			float conf = grp.m_confidence[j] * grp.m_windowsize[j] / maxConfVec[i];
			rotPatch = cv::Vec3f(conf,conf,conf);
			MozacPatch(canvas,rotPatch,sep,confPIdx); //next cnt
			pindx ++;
			beginPatchIndex ++;
		}
		beginPatchIndex ++;
	}

}

void TexturePatchGS::VisAllGrp(std::string basePath, int chainID){

	if (chainID < 0 )
	{
		vec vec_bk = m_txChains;
		std::sort(m_txChains.begin(),m_txChains.end(),ChainSizeGreat);
		int chainCnt = m_txChains.size();
		//int chainCnt = m_txChains.size() > 20? 20 : m_txChains.size();
		for (int i  = 0; i < chainCnt; i++)
		{
			VisAllGrp(basePath,i);
		}
		m_txChains = vec_bk;
	}
	else{
		SuperPixel& sp = m_txChains[chainID];
		int patchCnt = sp.m_pixelID.size();

		if(patchCnt < 2)
			return;

		int hCnt = sqrt((float)patchCnt) + 1;
		int vCnt = hCnt; 
		int patSep = 1;

#ifdef __CANVAS__
		mat_3f rgbCanvas = CreateMozacCanvas(hCnt,vCnt,m_patchsize,patSep);
		mat_3f chromCanvas = rgbCanvas.clone();
#endif
		int* pixID = &(sp.m_pixelID[0]);
		int* rot = &(sp.m_rotation[0]); 

		int ih = m_dmPtr->getImgSize().height;
		int iw = m_dmPtr->getImgSize().width;

		mat_3f& inputImg = m_dmPtr->getInput();
		mat_3f& chromImg = m_dmPtr->getChrom();


		mat_3f patch = mat_3f(m_patchsize,m_patchsize);
		mat_3f rotPatch = patch.clone();

		int halfsize = m_patchsize >> 1;

		char buffer[256];

		for (int i = 0; i < patchCnt; i++)
		{

			int cx = sp.m_pixelID[i] % iw; //center x
			int cy = sp.m_pixelID[i] / iw; //center y
			int cr = sp.m_rotation[i]; //rotation angle


#ifdef __CANVAS__
			FetchPatch(inputImg,cy - halfsize, cx - halfsize, patch);
			PatchRotation(patch,rotPatch, cr);

			MozacPatch(rgbCanvas,rotPatch,patSep,i);
#endif

#ifdef __CANVAS__
			FetchPatch(chromImg,cy - halfsize, cx - halfsize, patch);
			PatchRotation(patch,rotPatch,cr);
			MozacPatch(chromCanvas,rotPatch,patSep,i);
#endif

		}
#ifdef __CANVAS__
		sprintf(buffer,"%s/chain_%08d_rgb.png",basePath.c_str(),chainID);
		cv::imwrite(std::string(buffer),rgbCanvas * 255.0);
		sprintf(buffer,"%s/chain_%08d_chrom.png",basePath.c_str(),chainID);
		cv::imwrite(std::string(buffer),chromCanvas * 255.0);
#endif
	}


}

void TexturePatchGS::Texturematch(void)
{
	int nsize = m_iWidth * m_iHeight;

	if(m_txPixelId.empty())
		return;

	// texture Match with the minmum window
	Cluster(m_txPixelId, m_patchsize);

	// check larger windows
	int windowsize = m_patchsize;

	for(int i=1; i<PATCHSCALENUM; i++)
	{
		windowsize += 2;

		CheckLargerWindow(windowsize);
	}

}

void TexturePatchGS::SetTxPixels()
{

	mat_3f& inputImg = m_dmPtr->getInput();
	mat_3f& chromImg = m_dmPtr->getChrom();

	int n, nchain;
	n = m_iWidth * m_iHeight;

	for(int i=0; i<n; i++)
	{
		m_txPixels[i].m_chainId.clear();
		m_txPixels[i].m_confidence.clear();
	}

	nchain = m_txChains.size();

	std::cout<<"# of chains:"<<nchain<<std::endl;

	for(int i=0; i<nchain; i++)
	{
		int *id, *windowsize, k;
		float *confidence, a, Imax(0);

		id = &m_txChains[i].m_pixelID[0];
		windowsize = &m_txChains[i].m_windowsize[0];
		confidence = &m_txChains[i].m_confidence[0];
		k = m_txChains[i].m_pixelID.size();

		while(k--)
		{
			float maxconf(0), val[3];
			TxPixel &P = m_txPixels[id[k]];			
			a = confidence[k]*windowsize[k];
			// put the best match at the first
			if(!P.m_chainId.empty())
				maxconf = P.m_confidence[0];
			if(maxconf>a)
			{
				P.m_chainId.push_back(i);
				P.m_confidence.push_back(a);
			}else
			{
				P.m_chainId.insert(P.m_chainId.begin(), i);
				P.m_confidence.insert(P.m_confidence.begin(), a);
			}

			cv::Vec3f pixVal = inputImg(id[k]/m_iWidth,id[k]%m_iWidth);
			val[0] = pixVal[0];
			val[1] = pixVal[1];
			val[2] = pixVal[2];
			//			m_pfmInputImg.GetPixelValue(id[k], 0, val);

			Imax = std::max(Imax, val[0]*val[0] + val[1]*val[1] + val[2]*val[2]);
		}
		m_txChains[i].m_Imax = sqrt(Imax);
	}

	for(int i=0; i<n; i++)
	{
		if(m_txPixels[i].m_chainId.empty())
		{
			SuperPixel S;
			float val[3];

			m_txPixels[i].m_chainId.push_back(nchain);
			m_txPixels[i].m_confidence.push_back(1.0);

			cv::Vec3f chromVal = chromImg(i/m_iWidth,i%m_iWidth);
			S.m_chrom[0] = chromVal[0];
			S.m_chrom[1] = chromVal[1];
			S.m_chrom[2] = chromVal[2];


			//			m_pfmChromImg.GetPixelValue(i, 0, S.m_chrom);
			S.m_pixelID.push_back(i);
			S.m_windowsize.push_back(1);
			S.m_confidence.push_back(1.0);
			S.m_rotation.push_back(0);

			cv::Vec3f pixVal = inputImg(i/m_iWidth,i%m_iWidth);
			val[0] = pixVal[0];
			val[1] = pixVal[1];
			val[2] = pixVal[2];

			//			m_pfmInputImg.GetPixelValue(i, 0, val);
			S.m_Imax = sqrt(val[0]*val[0] + val[1]*val[1] + val[2]*val[2]);
			m_txChains.push_back(S);
			nchain++;
		}
	}
}

void TexturePatchGS::chains2groups(){
	//
	for(int i=0;i<m_txChains.size();i++){
		SuperPixel& sp = m_txChains[i];
		GrpEle ge;
		ge.m_grpType = REF;
		ge.m_gID = i;
		for(int j=0;j<sp.m_pixelID.size();j++)
		{
			int windowSize = sp.m_windowsize[j];
			float conf = sp.m_confidence[j];

			ge.m_eMember.push_back(Element(sp.m_pixelID[j], windowSize * conf));
		}
		m_groups.push_back(ge);
	}
#ifdef __OPT_DEBUG__
	m_eleCnt = m_iWidth * m_iHeight;
	for(int i=0; i < m_eleCnt;i++){
		TxPixel& tp = m_txPixels[i];
		EleGrp eg;
		eg.m_eID = i;
		eg.m_mcShadingGrpIdx = eg.m_mcShadingVectPos = -1;
		eg.m_mcRefVectPos = 0;
		eg.m_mcRefGrpIdx = tp.m_chainId[0];
		for(int j=0;j<tp.m_chainId.size();j++)
			eg.m_gMember.push_back(Element(tp.m_chainId[j],tp.m_confidence[j]));
		m_elements.push_back(eg);
	}
#endif
}

float TexturePatchGS::updateGrpConf(int grpID, int pixID){
	TxPixel& tp = m_txPixels[pixID];
	for(int i=0;i<tp.m_chainId.size();i++){
		if(tp.m_chainId[i] == grpID)
			return tp.m_confidence[i];
	}
	return 0;
}

int TexturePatchGS::IsIn(int p, vect_i & v){
	int num, *val;
	if(v.empty()) return -1;

	num = v.size();
	val = &v[0];

	while(num--){
		if (val[num] == p)
			break;
	}
	return num;

}

TexturePatchGS::~TexturePatchGS()
{
	//	if(m_txPixels)
	//		delete[] m_txPixels;
}

void TexturePatchGS::printTxChains(std::string fileName){
	FILE* fid = fopen(fileName.c_str(),"w");
	for(int i=0;i<m_txChains.size();i++){
		SuperPixel& sp = m_txChains[i];
		fprintf(fid,"%d ",i);
		for(int j=0;j<sp.m_pixelID.size();j++){
			fprintf(fid,"%d %f %d ",sp.m_pixelID[j],sp.m_confidence[j],sp.m_windowsize[j]);
		}
		fprintf(fid,"\n");
	}
	fclose(fid);
}

void TexturePatchGS::printTxPixels(std::string fileName){
	FILE* fid = fopen(fileName.c_str(),"w");

	int pixCnt = m_iWidth * m_iHeight;
	for(int i=0;i<pixCnt;i++){
		TxPixel& tp = m_txPixels[i];
		fprintf(fid,"%d ",i);
		for(int j=0;j<tp.m_chainId.size();j++){
			fprintf(fid,"%d %f ",tp.m_chainId[j],tp.m_confidence[j]);
		}
		fprintf(fid,"\n");
	}
	fclose(fid);

}

void TexturePatchGS::_group(){

	m_txChains.clear();
	m_txPixelId.clear();
	m_iWidth = m_dmPtr->getImgSize().width;
	m_iHeight = m_dmPtr->getImgSize().height;
	m_txPixels = std::vector<TxPixel>(m_iWidth*m_iHeight);
	buildTxPool();
	Texturematch();
	//now refine the groups
#ifdef __REFINE_GRP__
	for (int i = 0; i < m_txChains.size(); i++)
	{
		SuperPixel& grp = m_txChains[i];
		RefineGrp(grp); //refine the group
	}
	
#endif
	SetTxPixels();
	//printTxChains("d:/tx_chains1.txt");
	chains2groups();
	getGrpMaxInt();
	getGrpChrom();
	m_eleCnt = m_iWidth * m_iHeight;

}


