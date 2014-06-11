#!/bin/bash
set -x
export LD_LIBRARY_PATH=/home/sbell/opt/OpenCV-2.1.0/build/lib:/usr/local/MATLAB/R2011b/bin/glnxa64:/usr/local/MATLAB/R2011b/sys/os/glnxa64:/home/sbell/mitsuba/dist:/usr/local/cuda-5.5/lib64:/opt/intel/composer_xe_2013_sp1/mkl/lib/intel64:/opt/intel/composer_xe_2013_sp1.1.106/ipp/../compiler/lib/intel64:/opt/intel/composer_xe_2013_sp1.1.106/compiler/lib/intel64:/opt/intel/composer_xe_2013_sp1.1.106/ipp/lib/intel64:/opt/intel/composer_xe_2013_sp1.1.106/mkl/lib/intel64:/opt/intel/composer_xe_2013_sp1/lib/intel64:/opt/intel/composer_xe_2013_sp1.1.106/mpirt/lib/intel64:/opt/intel/composer_xe_2013_sp1.1.106/tbb/lib/intel64/gcc4.4:/home/sbell/mitsuba/dist:/usr/local/cuda-5.5/lib64:/opt/intel/composer_xe_2013_sp1/mkl/lib/intel64:/opt/intel/composer_xe_2013_sp1.1.106/ipp/../compiler/lib/intel64:/opt/intel/composer_xe_2013_sp1.1.106/compiler/lib/intel64:/opt/intel/composer_xe_2013_sp1.1.106/ipp/lib/intel64:/opt/intel/composer_xe_2013_sp1.1.106/mkl/lib/intel64:/opt/intel/composer_xe_2013_sp1/lib/intel64:/opt/intel/composer_xe_2013_sp1.1.106/mpirt/lib/intel64:/opt/intel/composer_xe_2013_sp1.1.106/tbb/lib/intel64/gcc4.4::/usr/lib:/usr/local/lib:/opt/lux:/usr/lib:/usr/local/lib:/opt/lux

img=$1
shift
./build/release/intrinsic_soe -i $img -o ./ $@
