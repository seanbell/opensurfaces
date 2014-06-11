%This code has been tested in Matlab 7.11.0(R2010b), using an Intel(R)
%Core(TM)i7-2630QM with CPU @ 2.00GHz, 8.00GB RAM and 64-bit operating
%system (Windows 7).

%im --> h x w x 3 image. 
%   valid im formats: uint8, uint16, uint32, double.
%param --> cell of optional parameters {par,val,RADpar,logar,mask}
%   par: 2-array containing the weights of the unary and 
%       pair-wise terms of the energy function respectively.
%       Default: par=[2,1].
%   val: 3-cell containing the values of the 3 different
%       scenarios that modify the weight of the pair-wise term.
%       Default: val={0.5,500,750};
%   RADpar: RAD integraparameters. Default: RAD=[1.5,0.01] 
%   logar states when the logarithm of the image is used. Not used when 
%       logar=0, used otherwise. Default: logar=1;
%   mask is a binary h x w image defining the pixels in the image that are
%       foreground. Default: mask={};

load prova_test.mat;
im = imread('input.bmp');
[refl,shad]=main(im,param);
%figure;imshow(refl);
%figure;imshow(shad);
imwrite(refl, 'reflectance.bmp');
