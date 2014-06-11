g_name='input.png';
[reflectance shading] = IntrinsicImage_GS_Automatic(g_name,wd,100,rho,unmap_srgb);
imwrite(reflectance, 'reflectance.png')
imwrite(shading, 'shading.png')
