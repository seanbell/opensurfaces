/*
 * PixelGroup.cpp
 *
 *  Created on: 2010-1-6
 *      Author: zhaoqi
 */

#include "PixelGroup.h"
#include <stdio.h>

void PixelGroup::readFromFile(FILE* fid) {
	fread(&m_refIndex,sizeof(m_refIndex),1,fid);
	//
	int pixCnt;
	fread(&pixCnt,sizeof(pixCnt),1,fid);
	for(int i=0; i<pixCnt; i++){
		int tmpPixId;
		float tmpPixConf;
		fread(&tmpPixId,sizeof(tmpPixId),1,fid);
		fread(&tmpPixConf,sizeof(tmpPixConf),1,fid);
		m_pixelID.push_back(tmpPixId);
		m_conf.push_back(tmpPixConf);
	}
	//
	fread(&m_chrom[0], sizeof(m_chrom[0]), 1, fid);
	fread(&m_chrom[1], sizeof(m_chrom[1]), 1, fid);
	fread(&m_chrom[1], sizeof(m_chrom[1]), 1, fid);
	//
	fread(&m_rgb[0], sizeof(m_rgb[0]), 1, fid);
	fread(&m_rgb[1], sizeof(m_rgb[1]), 1, fid);
	fread(&m_rgb[1], sizeof(m_rgb[1]), 1, fid);
	//
	fread(&m_maxIntensity, sizeof(m_maxIntensity), 1, fid);
	//
}

void PixelGroup::writeToFile(FILE* fid) {
	//write chrom value
	fwrite(&m_refIndex, sizeof(m_refIndex), 1, fid);
	int pixCnt = m_pixelID.size();
	fwrite(&pixCnt, sizeof(pixCnt), 1, fid);
	///write pixel id and confidence value
	for (int i=0; i<pixCnt; i++) {
		int tmpPixId = m_pixelID[i];
		int tmpPixConf = m_conf[i];
		fwrite(&tmpPixId, sizeof(tmpPixId), 1, fid);
		fwrite(&tmpPixConf, sizeof(tmpPixConf), 1, fid);
	}
	//write chrom and r
	fwrite(&m_chrom[0], sizeof(m_chrom[0]), 1, fid);
	fwrite(&m_chrom[1], sizeof(m_chrom[1]), 1, fid);
	fwrite(&m_chrom[1], sizeof(m_chrom[1]), 1, fid);
	//
	fwrite(&m_rgb[0], sizeof(m_rgb[0]), 1, fid);
	fwrite(&m_rgb[1], sizeof(m_rgb[1]), 1, fid);
	fwrite(&m_rgb[1], sizeof(m_rgb[1]), 1, fid);
	//
	fwrite(&m_maxIntensity, sizeof(m_maxIntensity), 1, fid);
}
