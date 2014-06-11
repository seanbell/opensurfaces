/*
 * AppConfig.h
 *
 *  Created on: 2010-1-6
 *      Author: zhaoqi
 */

#ifndef APPCONFIG_H_
#define APPCONFIG_H_

#define MRF_LABEL_NUM 40

struct AppConfig {
	static float m_shadingWeight;
	static float m_refWeight;
	static float m_chromChange_trd;
	static float m_chromVar_trd;
	static float m_pixDist_trd;
	static float m_normChange_trd;
	static int m_trw_iterCnt;
	static bool m_multMatch;
	static bool m_softMatch;
};

#endif /* APPCONFIG_H_ */
