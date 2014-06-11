%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% This is the matlab re-implementation according to the original
% opencv implementation code in cvpr11 paper:

%%%%%%%%%%%%%%% Intrinsic image by automatic algorithm using Equation (5) %%%%%%%%%%%%
clear all
close all

g_name='girl_small.bmp';
[reflectance shading] = IntrinsicImage_GS_Automatic(g_name,3,100,1.9);
imwrite(reflectance,'girl_R_wd3_iter100_rho1.9_Automatic.bmp');
imwrite(shading,'girl_S_wd3_iter100_rho1.9_Automatic.bmp');

subplot(1,3,1),imshow(imread(g_name)),title('Input');
subplot(1,3,2),imshow(reflectance),title('Reflectance');
subplot(1,3,3),imshow(shading),title('Shading');

% clear all

%%%%%%%%%%%%%%% Intrinsic image with user brushes using Equation (7) %%%%%%%%%%%%
clear all;
close all;

g_name='girl.bmp';
c_name='girl_brush.bmp';

brush_YorN = 1;

if brush_YorN
	[R_Tag S_Tag L_Tag] = ExtractBrushTag(imread(g_name),imread(c_name));
end
[reflectance shading] = IntrinsicImage_GS_Brush(g_name,3,100,1.9,brush_YorN,R_Tag,S_Tag,L_Tag,0.9,0.7);

imwrite(reflectance,'girl_R_wd3_iter100_rho1.9_Brush.bmp');
imwrite(shading,'girl_S_wd3_iter100_rho1.9_Brush.bmp');

subplot(1,3,1),imshow(imread(c_name));
subplot(1,3,2),imshow(reflectance);
subplot(1,3,3),imshow(shading);

% clear all
