function [I,R,S,C,mask] = mitLoad(imname, test)

imdir = [getDataDir(),imname,'/'];


% we load the diffuse and not the original image as in the MIT code!
I = imread([imdir,'diffuse.png']);
if test
  R = imread([imdir,'reflectance.png']);
  S = imread([imdir,'shading.png']);
  C = imread([imdir,'specular.png']);
else
  R = [];
  S = [];
  C = [];
end

if exist([imdir,'mask.png'], 'file')
  mask = imread([imdir,'mask.png']);
else
  mask = ones(size(I, 1), size(I, 2));
end

I = double(I);
R = double(R);
S = double(S);
C = double(C);
mask = double(mask);

I = I./(2^16-1);
R = R./(2^16-1);
S = S./(2^16-1);
C = C./(2^16-1);
mask(mask>0) = 1;
