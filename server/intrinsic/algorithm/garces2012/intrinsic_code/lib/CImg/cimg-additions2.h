#ifndef _CIMG_ADDITIONS_H_
#define _CIMG_ADDITIONS_H_

/* THIS CODE CARRIES NO GUARANTEE OF USABILITY OR FITNESS FOR ANY PURPOSE.
 * WHILE THE AUTHORS HAVE TRIED TO ENSURE THE PROGRAM WORKS CORRECTLY,
 * IT IS STRICTLY USE AT YOUR OWN RISK.  */

/* utility for reading and writing Ward's rgbe image format.
   See rgbe.txt file for more details.
*/


private:

typedef struct {
  int valid;            /* indicate which fields are valid */
  char programtype[16]; /* listed at beginning of file to identify it 
                         * after "#?".  defaults to "RGBE" */ 
  float gamma;          /* image has already been gamma corrected with 
                         * given gamma.  defaults to 1.0 (no correction) */
  float exposure;       /* a value of 1.0 in an image corresponds to
			 * <exposure> watts/steradian/m^2. 
			 * defaults to 1.0 */
} rgbe_header_info;

/* flags indicating which fields in an rgbe_header_info are valid */
#define RGBE_VALID_PROGRAMTYPE 0x01
#define RGBE_VALID_GAMMA       0x02
#define RGBE_VALID_EXPOSURE    0x04

/* return codes for rgbe routines */
#define RGBE_RETURN_SUCCESS 0
#define RGBE_RETURN_FAILURE -1

/* offsets to red, green, and blue components in a data (float) pixel */
#define RGBE_DATA_RED    0
#define RGBE_DATA_GREEN  1
#define RGBE_DATA_BLUE   2
/* number of floats per pixel */
#define RGBE_DATA_SIZE   3

enum rgbe_error_codes {
  rgbe_read_error,
  rgbe_write_error,
  rgbe_format_error,
  rgbe_memory_error,
};

/* default error routine.  change this to change error handling */
static int rgbe_error(int rgbe_error_code, const char *msg)
{
  switch (rgbe_error_code) {
  case rgbe_read_error:
    perror("RGBE read error");
    break;
  case rgbe_write_error:
    perror("RGBE write error");
    break;
  case rgbe_format_error:
    fprintf(stderr,"RGBE bad file format: %s\n",msg);
    break;
  default:
  case rgbe_memory_error:
    fprintf(stderr,"RGBE error: %s\n",msg);
  }
  return RGBE_RETURN_FAILURE;
}

/* standard conversion from float pixels to rgbe pixels */
/* note: you can remove the "inline"s if your compiler complains about it */
static inline void
float2rgbe(unsigned char rgbe[4], float red, float green, float blue)
{
  float v;
  int e;

  v = red;
  if (green > v) v = green;
  if (blue > v) v = blue;
  if (v < 1e-32) {
    rgbe[0] = rgbe[1] = rgbe[2] = rgbe[3] = 0;
  }
  else {
    v = frexp(v,&e) * 256.0/v;
    rgbe[0] = (unsigned char) (red * v);
    rgbe[1] = (unsigned char) (green * v);
    rgbe[2] = (unsigned char) (blue * v);
    rgbe[3] = (unsigned char) (e + 128);
  }
}

/* standard conversion from rgbe to float pixels */
/* note: Ward uses ldexp(col+0.5,exp-(128+8)).  However we wanted pixels */
/*       in the range [0,1] to map back into the range [0,1].            */
static inline void
rgbe2float(float *red, float *green, float *blue, unsigned char rgbe[4])
{
  float f;

  if (rgbe[3]) {   /*nonzero pixel*/
    f = ldexp(1.0,rgbe[3]-(int)(128+8));
    *red = rgbe[0] * f;
    *green = rgbe[1] * f;
    *blue = rgbe[2] * f;
  }
  else
    *red = *green = *blue = 0.0f;
}

/* default minimal header. modify if you want more information in header */
static int RGBE_WriteHeader(FILE *fp, int width, int height, rgbe_header_info *info)
{
  char default_program_type[]="RGBE";
  char *programtype = default_program_type;

  if (info && (info->valid & RGBE_VALID_PROGRAMTYPE))
    programtype = info->programtype;
  if (fprintf(fp,"#?%s\n",programtype) < 0)
    return rgbe_error(rgbe_write_error,NULL);
  /* The #? is to identify file type, the programtype is optional. */
  if (info && (info->valid & RGBE_VALID_GAMMA)) {
    if (fprintf(fp,"GAMMA=%g\n",info->gamma) < 0)
      return rgbe_error(rgbe_write_error,NULL);
  }
  if (info && (info->valid & RGBE_VALID_EXPOSURE)) {
    if (fprintf(fp,"EXPOSURE=%g\n",info->exposure) < 0)
      return rgbe_error(rgbe_write_error,NULL);
  }
  if (fprintf(fp,"FORMAT=32-bit_rle_rgbe\n\n") < 0)
    return rgbe_error(rgbe_write_error,NULL);
  if (fprintf(fp, "-Y %d +X %d\n", height, width) < 0)
    return rgbe_error(rgbe_write_error,NULL);
  return RGBE_RETURN_SUCCESS;
}

/* minimal header reading.  modify if you want to parse more information */
static int RGBE_ReadHeader(FILE *fp, int *width, int *height, rgbe_header_info *info)
{
  char buf[128];
  int found_format;
  float tempf;
  unsigned int i;

  found_format = 0;
  if (info) {
    info->valid = 0;
    info->programtype[0] = 0;
    info->gamma = info->exposure = 1.0;
  }
  if (fgets(buf,sizeof(buf)/sizeof(buf[0]),fp) == NULL)
    return rgbe_error(rgbe_read_error,NULL);
  if ((buf[0] != '#')||(buf[1] != '?')) {
    /* if you want to require the magic token then uncomment the next line */
    /*return rgbe_error(rgbe_format_error,"bad initial token"); */
  }
  else if (info) {
    info->valid |= RGBE_VALID_PROGRAMTYPE;
    for(i=0;i<sizeof(info->programtype)-1;i++) {
      if ((buf[i+2] == 0) || isspace(buf[i+2]))
	break;
      info->programtype[i] = buf[i+2];
    }
    info->programtype[i] = 0;
    if (fgets(buf,sizeof(buf)/sizeof(buf[0]),fp) == 0)
      return rgbe_error(rgbe_read_error,NULL);
  }
  for(;;) {
    if ((buf[0] == 0)||(buf[0] == '\n'))
      return rgbe_error(rgbe_format_error,"no FORMAT specifier found");
    else if (strcmp(buf,"FORMAT=32-bit_rle_rgbe\n") == 0)
      break;       /* format found so break out of loop */
    else if (info && (sscanf(buf,"GAMMA=%g",&tempf) == 1)) {
      info->gamma = tempf;
      info->valid |= RGBE_VALID_GAMMA;
    }
    else if (info && (sscanf(buf,"EXPOSURE=%g",&tempf) == 1)) {
      info->exposure = tempf;
      info->valid |= RGBE_VALID_EXPOSURE;
    }
    if (fgets(buf,sizeof(buf)/sizeof(buf[0]),fp) == 0)
      return rgbe_error(rgbe_read_error,NULL);
  }
  if (fgets(buf,sizeof(buf)/sizeof(buf[0]),fp) == 0)
    return rgbe_error(rgbe_read_error,NULL);
  if (strcmp(buf,"\n") != 0)
    return rgbe_error(rgbe_format_error,
		      "missing blank line after FORMAT specifier");
  if (fgets(buf,sizeof(buf)/sizeof(buf[0]),fp) == 0)
    return rgbe_error(rgbe_read_error,NULL);
  if (sscanf(buf,"-Y %d +X %d",height,width) < 2)
    return rgbe_error(rgbe_format_error,"missing image size specifier");
  return RGBE_RETURN_SUCCESS;
}

/* simple write routine that does not use run length encoding */
/* These routines can be made faster by allocating a larger buffer and
   fread-ing and fwrite-ing the data in larger chunks */
static int RGBE_WritePixels(FILE *fp, float *data, int numpixels)
{
  unsigned char rgbe[4];

  while (numpixels-- > 0) {
    float2rgbe(rgbe,data[RGBE_DATA_RED],
	       data[RGBE_DATA_GREEN],data[RGBE_DATA_BLUE]);
    data += RGBE_DATA_SIZE;
    if (fwrite(rgbe, sizeof(rgbe), 1, fp) < 1)
      return rgbe_error(rgbe_write_error,NULL);
  }
  return RGBE_RETURN_SUCCESS;
}

/* simple read routine.  will not correctly handle run length encoding */
static int RGBE_ReadPixels(FILE *fp, float *data, int numpixels)
{
  unsigned char rgbe[4];

  while(numpixels-- > 0) {
    if (fread(rgbe, sizeof(rgbe), 1, fp) < 1)
      return rgbe_error(rgbe_read_error,NULL);
    rgbe2float(&data[RGBE_DATA_RED],&data[RGBE_DATA_GREEN],
	       &data[RGBE_DATA_BLUE],rgbe);
    data += RGBE_DATA_SIZE;
  }
  return RGBE_RETURN_SUCCESS;
}

/* The code below is only needed for the run-length encoded files. */
/* Run length encoding adds considerable complexity but does */
/* save some space.  For each scanline, each channel (r,g,b,e) is */
/* encoded separately for better compression. */

static int RGBE_WriteBytes_RLE(FILE *fp, unsigned char *data, int numbytes)
{
#define MINRUNLENGTH 4
  int cur, beg_run, run_count, old_run_count, nonrun_count;
  unsigned char buf[2];

  cur = 0;
  while(cur < numbytes) {
    beg_run = cur;
    /* find next run of length at least 4 if one exists */
    run_count = old_run_count = 0;
    while((run_count < MINRUNLENGTH) && (beg_run < numbytes)) {
      beg_run += run_count;
      old_run_count = run_count;
      run_count = 1;
      while((data[beg_run] == data[beg_run + run_count])
	    && (beg_run + run_count < numbytes) && (run_count < 127))
	run_count++;
    }
    /* if data before next big run is a short run then write it as such */
    if ((old_run_count > 1)&&(old_run_count == beg_run - cur)) {
      buf[0] = 128 + old_run_count;   /*write short run*/
      buf[1] = data[cur];
      if (fwrite(buf,sizeof(buf[0])*2,1,fp) < 1)
	return rgbe_error(rgbe_write_error,NULL);
      cur = beg_run;
    }
    /* write out bytes until we reach the start of the next run */
    while(cur < beg_run) {
      nonrun_count = beg_run - cur;
      if (nonrun_count > 128)
	nonrun_count = 128;
      buf[0] = nonrun_count;
      if (fwrite(buf,sizeof(buf[0]),1,fp) < 1)
	return rgbe_error(rgbe_write_error,NULL);
      if (fwrite(&data[cur],sizeof(data[0])*nonrun_count,1,fp) < 1)
	return rgbe_error(rgbe_write_error,NULL);
      cur += nonrun_count;
    }
    /* write out next run if one was found */
    if (run_count >= MINRUNLENGTH) {
      buf[0] = 128 + run_count;
      buf[1] = data[beg_run];
      if (fwrite(buf,sizeof(buf[0])*2,1,fp) < 1)
	return rgbe_error(rgbe_write_error,NULL);
      cur += run_count;
    }
  }
  return RGBE_RETURN_SUCCESS;
#undef MINRUNLENGTH
}

static int RGBE_WritePixels_RLE(FILE *fp, float *data, int scanline_width,
			 int num_scanlines)
{
  unsigned char rgbe[4];
  unsigned char *buffer;
  int i, err;

  if ((scanline_width < 8)||(scanline_width > 0x7fff))
    /* run length encoding is not allowed so write flat*/
    return RGBE_WritePixels(fp,data,scanline_width*num_scanlines);
  buffer = (unsigned char *)malloc(sizeof(unsigned char)*4*scanline_width);
  if (buffer == NULL)
    /* no buffer space so write flat */
    return RGBE_WritePixels(fp,data,scanline_width*num_scanlines);
  while(num_scanlines-- > 0) {
    rgbe[0] = 2;
    rgbe[1] = 2;
    rgbe[2] = scanline_width >> 8;
    rgbe[3] = scanline_width & 0xFF;
    if (fwrite(rgbe, sizeof(rgbe), 1, fp) < 1) {
      free(buffer);
      return rgbe_error(rgbe_write_error,NULL);
    }
    for(i=0;i<scanline_width;i++) {
      float2rgbe(rgbe,data[RGBE_DATA_RED],
		 data[RGBE_DATA_GREEN],data[RGBE_DATA_BLUE]);
      buffer[i] = rgbe[0];
      buffer[i+scanline_width] = rgbe[1];
      buffer[i+2*scanline_width] = rgbe[2];
      buffer[i+3*scanline_width] = rgbe[3];
      data += RGBE_DATA_SIZE;
    }
    /* write out each of the four channels separately run length encoded */
    /* first red, then green, then blue, then exponent */
    for(i=0;i<4;i++) {
      if ((err = RGBE_WriteBytes_RLE(fp,&buffer[i*scanline_width],
				     scanline_width)) != RGBE_RETURN_SUCCESS) {
	free(buffer);
	return err;
      }
    }
  }
  free(buffer);
  return RGBE_RETURN_SUCCESS;
}

static int RGBE_ReadPixels_RLE(FILE *fp, float *data, int scanline_width,
			int num_scanlines)
{
  unsigned char rgbe[4], *scanline_buffer, *ptr, *ptr_end;
  int i, count;
  unsigned char buf[2];

  if ((scanline_width < 8)||(scanline_width > 0x7fff))
    /* run length encoding is not allowed so read flat*/
    return RGBE_ReadPixels(fp,data,scanline_width*num_scanlines);
  scanline_buffer = NULL;
  /* read in each successive scanline */
  while(num_scanlines > 0) {
    if (fread(rgbe,sizeof(rgbe),1,fp) < 1) {
      free(scanline_buffer);
      return rgbe_error(rgbe_read_error,NULL);
    }
    if ((rgbe[0] != 2)||(rgbe[1] != 2)||(rgbe[2] & 0x80)) {
      /* this file is not run length encoded */
      rgbe2float(&data[0],&data[1],&data[2],rgbe);
      data += RGBE_DATA_SIZE;
      free(scanline_buffer);
      return RGBE_ReadPixels(fp,data,scanline_width*num_scanlines-1);
    }
    if ((((int)rgbe[2])<<8 | rgbe[3]) != scanline_width) {
      free(scanline_buffer);
      return rgbe_error(rgbe_format_error,"wrong scanline width");
    }
    if (scanline_buffer == NULL)
      scanline_buffer = (unsigned char *)
	malloc(sizeof(unsigned char)*4*scanline_width);
    if (scanline_buffer == NULL)
      return rgbe_error(rgbe_memory_error,"unable to allocate buffer space");

    ptr = &scanline_buffer[0];
    /* read each of the four channels for the scanline into the buffer */
    for(i=0;i<4;i++) {
      ptr_end = &scanline_buffer[(i+1)*scanline_width];
      while(ptr < ptr_end) {
	if (fread(buf,sizeof(buf[0])*2,1,fp) < 1) {
	  free(scanline_buffer);
	  return rgbe_error(rgbe_read_error,NULL);
	}
	if (buf[0] > 128) {
	  /* a run of the same value */
	  count = buf[0]-128;
	  if ((count == 0)||(count > ptr_end - ptr)) {
	    free(scanline_buffer);
	    return rgbe_error(rgbe_format_error,"bad scanline data");
	  }
	  while(count-- > 0)
	    *ptr++ = buf[1];
	}
	else {
	  /* a non-run */
	  count = buf[0];
	  if ((count == 0)||(count > ptr_end - ptr)) {
	    free(scanline_buffer);
	    return rgbe_error(rgbe_format_error,"bad scanline data");
	  }
	  *ptr++ = buf[1];
	  if (--count > 0) {
	    if (fread(ptr,sizeof(*ptr)*count,1,fp) < 1) {
	      free(scanline_buffer);
	      return rgbe_error(rgbe_read_error,NULL);
	    }
	    ptr += count;
	  }
	}
      }
    }
    /* now convert data from buffer into floats */
    for(i=0;i<scanline_width;i++) {
      rgbe[0] = scanline_buffer[i];
      rgbe[1] = scanline_buffer[i+scanline_width];
      rgbe[2] = scanline_buffer[i+2*scanline_width];
      rgbe[3] = scanline_buffer[i+3*scanline_width];
      rgbe2float(&data[RGBE_DATA_RED],&data[RGBE_DATA_GREEN],
		 &data[RGBE_DATA_BLUE],rgbe);
      data += RGBE_DATA_SIZE;
    }
    num_scanlines--;
  }
  free(scanline_buffer);
  return RGBE_RETURN_SUCCESS;
}

public:
const CImg<T>& save_hdr(const char* filename) const
{
	if (!filename)
		throw CImgArgumentException(_cimg_instance
	                                    "save_hdr() : Specified filename is (null).",
	                                    cimg_instance);
	
	std::FILE* f = cimg::fopen(filename,"wb");

	if (!f) 
	{
		cimg::fclose(f);
    		throw CImgIOException(_cimg_instance
                              "save_hdr() : Could not open HDR file '%s'.",
                              cimg_instance,
                              filename?filename:"(FILE*)");
	}
	RGBE_WriteHeader(f,this->width(),this->height(),0);

	float* buffer=new float[3*this->width()];

// There might be negative numbers after the conversion. rgbe does not support
// negative numbers propperly, so we eliminate them (two options: offsetting
// the whole image or putting negatives to 0.

        for (int i=0; i<this->height(); i++)
        {
            int idx = 0;
            for (int j=0; j<this->width(); j++,idx+=3)
            {
                    buffer[idx  ] = std::max((*this)(j,i,0),(T)0.0);
                    buffer[idx+1] = std::max((*this)(j,i,(spectrum()<1)?0:1),(T)0.0);
                    buffer[idx+2] = std::max((*this)(j,i,(spectrum()<2)?0:2),(T)0.0);
            }
            RGBE_WritePixels_RLE(f,buffer,this->width(),1);
        }

	cimg::fclose(f);
	return (*this);
}

CImg<T>& load_hdr(const char* filename)
{	
	if (!filename)
		throw CImgArgumentException(_cimg_instance
	                                    "load_hdr() : Specified filename is (null).",
	                                    cimg_instance);
	
	std::FILE* f = cimg::fopen(filename,"rb");

	if (!f) 
	{
		cimg::fclose(f);
    		throw CImgIOException(_cimg_instance
                              "load_hdr() : Could not open HDR file '%s'.",
                              cimg_instance,
                              filename);
	}

    	int width, height;
    	rgbe_header_info info;

    	if (RGBE_ReadHeader(f,&width,&height,&info)==RGBE_RETURN_FAILURE)
	{
		cimg::fclose(f);
    		throw CImgIOException(_cimg_instance
                              "load_hdr() : HDR header error '%s'.",
                              cimg_instance,
                              filename);
	}

	this->resize(width,height,1,3,-1);

	float* buffer = new float[3*width];

	for (int i=0; i<height; i++)
	{
		if (RGBE_ReadPixels_RLE(f,buffer,width,1)==RGBE_RETURN_FAILURE)
		{
			cimg::fclose(f);
	    		throw CImgIOException(_cimg_instance
		                      "load_hdr() : HDR reading error '%s'.",
		                      cimg_instance,
		                      filename);
		}

		int idx = 0;
		for (int j=0; j<width; j++,idx+=3)
			for (int c=0;c<3;c++)
				(*this)(j,i,c)=buffer[idx+c];
	}
	
	cimg::fclose(f);
	delete[] buffer;
	return (*this);
}

static CImg<T> get_load_hdr(std::FILE *const file) {
      return CImg<T>().load_hdr(file);
}

// The code below allows to add the support for the specified extension.
//---------------------------------------------------------------------
#ifndef cimg_load_plugin
#define cimg_load_plugin(filename) \
	  if (!cimg::strncasecmp(cimg::split_filename(filename),"hdr",3)) return load_hdr(filename);
#endif
#ifndef cimg_save_plugin
#define cimg_save_plugin(filename) \
	  if (!cimg::strncasecmp(cimg::split_filename(filename),"hdr",3)) return save_hdr(filename);
#endif


CImg<T>& clamp_min(float val = 0.0) {
	cimg_for(*this,ptrd,float) *ptrd=(*ptrd<val)?val:*ptrd;
	return *this;
}

template<typename Fv>
CImg<T>& draw_radial_functions(const float xc, const float yc, const Fv& f)
{
	float dy = -yc;
	const unsigned int whd = _width*_height*_depth;
	cimg_forY(*this,y) {
		float dx = -xc;
		cimg_forX(*this,x) {
			T *ptrd = this->data(x,y,0,0);
			float d = std::sqrt(dx*dx + dy*dy);
			cimg_forC(*this,c) { *ptrd = (T)(f[c](d)); ptrd+=whd; }
			++dx;
		}
		++dy;
	}
	return (*this);
}

template<typename F>
CImg<T>& draw_radial_function(const float xc, const float yc, const F& f)
{
	float dy = -yc;
	const unsigned int whd = _width*_height*_depth;
	cimg_forY(*this,y) {
		float dx = -xc;
		cimg_forX(*this,x) {
			T *ptrd = this->data(x,y,0,0);
			T v = (T)(f(std::sqrt(dx*dx + dy*dy)));
			cimg_forC(*this,c) { *ptrd = v; ptrd+=whd; }
			++dx;
		}
		++dy;
	}
	return (*this);
}

template<typename F>
CImg<T>& draw_radial_function(const float xc, const float yc, const F& fr, const F& fg, const F& fb)
{
	if (this->spectrum()!=3)
		throw CImgArgumentException(_cimg_instance
	                                    "draw_radial_function() : Should have spectrum()==3.",
	                                    cimg_instance);

	float dy = -yc;
	const unsigned int whd = _width*_height*_depth;
	cimg_forY(*this,y) {
		float dx = -xc;
		cimg_forX(*this,x) {
			T *ptrd = this->data(x,y,0,0);
			float d = std::sqrt(dx*dx + dy*dy);
			*ptrd = (T)(fr(d));
			ptrd+=whd;
			*ptrd = (T)(fg(d));
			ptrd+=whd;
			*ptrd = (T)(fb(d));
			++dx;
		}
		++dy;
	}
	return (*this);
}

CImg<T>& resize_bicubic(int width, int height)
{
	this->resize(width,height,1,3,5);
	return (*this);
}

CImg<T>& FFT_convolution(const CImg<T>& c) 
{
	CImg<T> this_real(*this);
	CImg<T> this_imag(this->width(),this->height(),1,3); this_imag.fill(0.0);
	CImg<T> conv_real(c); conv_real.resize_bicubic(this->width(),this->height());
	CImg<T> conv_imag(this->width(),this->height(),1,3); conv_imag.fill(0.0);
	
	CImg<T>::FFT(this_real,this_imag);
	CImg<T>::FFT(conv_real,conv_imag);

	*this =   (this_real.get_mul(conv_real)) - (this_imag.get_mul(conv_imag));
	CImg<T> imag(this_real.get_mul(conv_imag) + this_imag.get_mul(conv_real));

	CImg<T>::FFT(*this,imag,true);
	return (*this);
}

template<typename C>
CImg<T>& mul_color(const C& col)
{
	const unsigned int whd = _width*_height*_depth;
	cimg_forY(*this,y) {
		cimg_forX(*this,x) {
		T *ptrd = data(x,y,0,0);
		cimg_forC(*this,c) {
			*ptrd*=col[c];
			ptrd+=whd;
			}
		}
	}
	return (*this);
}

template<typename C>
CImg<T> get_mul_color(const C& c) const
{	return CImg<T>(*this).mul(c); }


template<typename C>
CImg<T> get_dot_product_C(const C& col) const
{
	CImg<T> sol(_width,_height,_depth,1);
	const unsigned int whd = _width*_height*_depth;
	cimg_forXYZ(*this,x,y,z) { 
		T& sol_ref = sol(x,y,0,0);
		const T *ptrd = data(x,y,0,0);
		sol_ref=0;
		cimg_forC(*this,c) {
			sol_ref+=(*ptrd)*col[c];
			ptrd+=whd;
		}
		
	}
	return sol;
}



#endif
