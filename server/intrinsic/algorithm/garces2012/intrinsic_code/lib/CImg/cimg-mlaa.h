#ifndef _CIMG_MLAA_H_
#define _CIMG_MLAA_H_

CImg<T>& mlaa(unsigned int pixelmode=0)
{
	unsigned char* buffer = new unsigned char[4*width()*height()];
	unsigned char* ptr_data=buffer;
    T
        *ptr_r = data(0,0,0,0),
        *ptr_g = spectrum()<=2?data(0,0,0,0):data(0,0,0,1),
        *ptr_b = spectrum()<=2?data(0,0,0,0):data(0,0,0,2),
        *ptr_a = spectrum()==2?data(0,0,0,2):(spectrum()==4)?data(0,0,0,4):NULL;
 
	//We copy the stuff to the mlaa buffer (called data)
        cimg_forY(*this,y) {
          cimg_forX(*this,x) {
	    *(ptr_data++) = (unsigned char)(*(ptr_r++));
	    *(ptr_data++) = (unsigned char)(*(ptr_g++));
	    *(ptr_data++) = (unsigned char)(*(ptr_b++));
	    if (ptr_a) *(ptr_data++) = (unsigned char)(*(ptr_a++)); else ++ptr_data;
          }
        }

  	{
    	RTTL::AtomicCounter job; 
	MLAA((unsigned int*)buffer,NULL,width(),height(),job,pixelmode);
	}

	ptr_data=buffer;
        ptr_r = data(0,0,0,0);
        ptr_g = spectrum()<=2?0:data(0,0,0,1);
        ptr_b = spectrum()<=2?0:data(0,0,0,2);
        ptr_a = spectrum()==2?data(0,0,0,2):(spectrum()==4)?data(0,0,0,4):NULL;
 
	//We copy the stuff to the mlaa buffer (called data)
        cimg_forY(*this,y) {
          cimg_forX(*this,x) {
	    *(ptr_r++) = (T)(*(ptr_data++));
	    if (ptr_g) *(ptr_g++) = (T)(*(ptr_data++)); else ++ptr_data;
	    if (ptr_b) *(ptr_b++) = (T)(*(ptr_data++)); else ++ptr_data;
	    if (ptr_a) *(ptr_a++) = (T)(*(ptr_data++)); else ++ptr_data;
         }
        }

	delete[] buffer;
	return (*this);
}

CImg<T> get_mlaa(int pixelmode = 0) const
{	return CImg<T>(*this).mlaa(pixelmode); }

#endif
