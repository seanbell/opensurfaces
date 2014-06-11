function bitify(path)
  r = uint16(imread([path 'reflectance.png'])) * 256;
  s = uint16(imread([path 'shading.png'])) * 256;
  s = s(:, :, 1);
  d = uint16(imread([path 'diffuse.png'])) * 256;
  m = uint16(imread([path 'mask.png'])) * 256;

  imwrite(r, [path 'reflectance.png']);
  imwrite(s, [path 'shading.png']);
  imwrite(m, [path 'specular.png']);
  m = m(:, :, 1);
  imwrite(m, [path 'mask.png']);
  imwrite(d, [path 'diffuse.png']);

