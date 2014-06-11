#ifndef TIMER_H_
#define TIMER_H_
#include <time.h>
#include <opencv/cxcore.h>

class Timer
{
protected:
	double m_beginT;
	double m_endT;
	double m_elapse; //in seconds
public:
	Timer();
	void start(){
		m_beginT  = cv::getTickCount();
		//gettimeofday(&m_beginT,0);
	}
	double stop(){
		m_endT = cv::getTickCount();
		m_elapse =  (m_endT - m_beginT) / cv::getTickFrequency();
		//gettimeofday(&m_endT,0);
		//m_elapse = (m_endT.tv_sec - m_beginT.tv_sec) + (m_endT.tv_usec - m_beginT.tv_usec) * 0.000001;
		
		return m_elapse;
	}
	double getElapse(){
		return m_elapse ;
	}
	virtual ~Timer();
};


#endif /*TIMER_H_*/
