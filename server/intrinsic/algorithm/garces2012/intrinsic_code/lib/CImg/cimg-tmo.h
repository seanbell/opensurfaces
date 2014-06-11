#ifndef _CIMG_TMO_H_
#define _CIMG_TMO_H_

//Tone mapper operators for CImg

/** REINHARD'02 **/
private:
CImg<T>& _tmo_reinhard02(Tfloat Lwhite, Tfloat a, Tfloat log_mean, const CImg<Tfloat>& l)
{
	Tfloat invLwhite2 = 1.0 / (Lwhite*Lwhite);

	cimg_forXYZ(*this,x,y,z)
	{	
		Tfloat lw = l(x,y,z,0);
		Tfloat al = (a/log_mean)*lw;
		Tfloat ld=(al*(1+al*invLwhite2))/(1+al);
		Tfloat f=(255.0*ld)/(lw*Lwhite);
		cimg_forC(*this,c) (*this)(x,y,z,c)=T(std::min(std::max(f*Tfloat((*this)(x,y,z,c))/Lwhite,Tfloat(0.0)),Tfloat(255.0)));
	}

	return *this;
}

public:
Tdouble log_mean() const
{	if (is_empty())
        	throw CImgInstanceException(_cimg_instance
                                    "log_mean() : Empty instance.",
                                    cimg_instance);
      		Tdouble res = 0;
      		cimg_for(*this,ptrs,T) res+=std::log(std::max((Tdouble)*ptrs,Tdouble(0.0001)));
      		return std::exp(res/size());
}

private:
CImg<T>& _tmo_reinhard02(Tfloat Lwhite, Tfloat a, const CImg<Tfloat>& l)
{
	return _tmo_reinhard02(Lwhite, a, l.log_mean(), l);
}

CImg<T>& _tmo_reinhard02(const CImg<Tfloat>& l)
{
	return _tmo_reinhard02(l.max(), 0.18, l.log_mean(), l);
}

public:

CImg<Tfloat> get_tmo_reinhard02_luminance() const
{
	if (spectrum()<3) return CImg<Tfloat>(this->get_channel(0));
	else 
	{	
		CImg<Tfloat> l(width(),height(),depth(),1);
		cimg_forXYZ(*this,x,y,z)
			l(x,y,z,0) = std::max(Tfloat(0.27)*Tfloat((*this)(x,y,z,0)) + 
						Tfloat(0.67)*Tfloat((*this)(x,y,z,1)) + 
						Tfloat(0.06)*Tfloat((*this)(x,y,z,2)),
				Tfloat(0.0));
		return l;	
	}
}
	

CImg<T>& tmo_reinhard02(Tfloat Lwhite, Tfloat a, Tfloat log_mean)
{	return _tmo_reinhard02(Lwhite,a,log_mean,get_tmo_reinhard02_luminance()); }

CImg<T>& tmo_reinhard02(Tfloat Lwhite, Tfloat a = 0.18)
{	return _tmo_reinhard02(Lwhite,a,get_tmo_reinhard02_luminance()); 	}

CImg<T>& tmo_reinhard02()
{	return _tmo_reinhard02(get_tmo_reinhard02_luminance()); 	}


CImg<T> get_tmo_reinhard02(Tfloat Lwhite, Tfloat a, Tfloat log_mean)
{	return CImg<T>(*this).tmo_reinhard02(Lwhite,a,log_mean); }

CImg<T> get_tmo_reinhard02(Tfloat Lwhite, Tfloat a = 0.18)
{	return CImg<T>(*this).tmo_reinhard02(Lwhite,a); }

CImg<T> get_tmo_reinhard02()
{	return CImg<T>(*this).tmo_reinhard02(); }



#endif
