function self = DiffTerm(img, parameter, opts)
  self = struct();

  self.estH = insertIntoMask(...
    trimToMask(colorRetEstimator(insertIntoMask(img.diffuse, img.mask), ...
    @get_gradients_x, parameter.thresholdGray, parameter.thresholdColor), ...
    img.mask), img.mask);
  self.estV = insertIntoMask(...
    trimToMask(colorRetEstimator(insertIntoMask(img.diffuse, img.mask), ...
    @get_gradients_y, parameter.thresholdGray, parameter.thresholdColor), ...
    img.mask), img.mask);

  if all(img.mask(:)==1)
    self.estV(end,:) = 0;
    self.estH(:,end) = 0;
  else
    for i=1:size(img.mask,1)
      ind1 = find(img.mask(i,:)==1);
      ind0 = find(img.mask(i,:)==0);

      % all those [0,1] crossings
      ind_01 = intersect(ind0+1,ind1);
      ind_10 = intersect(ind0-1,ind1);

      self.estH(i,ind_01) = 0;
      self.estV(i,ind_01) = 0;

      self.estH(i,ind_10) = 0;
      self.estV(i,ind_10) = 0;
    end

    for j=1:size(img.mask,2)
      ind1 = find(img.mask(:,j)==1);
      ind0 = find(img.mask(:,j)==0);

      ind_01 = intersect(ind0+1,ind1);
      ind_10 = intersect(ind0-1,ind1);

      self.estH(ind_01,j) = 0;
      self.estV(ind_01,j) = 0;

      self.estH(ind_10,j) = 0;
      self.estV(ind_10,j) = 0;
    end
  end

  self.estH = trimToMask(self.estH, img.mask);
  self.estV = trimToMask(self.estV, img.mask);

  self.laplacian = opts.laplacian;
  self.filterH = opts.filterH;
  self.filterV = opts.filterV;

  self.cretDerivativeTerm = self.filterH'*self.estH + self.filterV'*self.estV;

  self.getEnergy = @getEnergy;
  self.update = @update;
  self.putStats = @putStats;
end

function [E, dE] = getEnergy(self, r)
  logR = log(r+eps);
  filteredHR = self.filterH * logR;
  filteredVR = self.filterV * logR;

  laplacianR = self.laplacian * logR;

  % the last two terms are not necessary for the optimization
  %E = logR' * LR + 2*sum( (LhR .* self.r_x) + (LvR .* self.r_y) )...
    %+ sum(self.r_x.^2) + sum(self.r_y.^2);
  E = logR' * laplacianR + 2*sum((filteredHR.*self.estH) + (filteredVR.*self.estV));

  %dE =  2* LR + 2 * (opts.Lh' * r_x + opts.Lv' * r_y);
  dE =  2* laplacianR + 2 * self.cretDerivativeTerm;

  dE = (dE./r);
end

function self = update(self, R)
end

function stats = putStats(self, stats)
end

function [est] = colorRetEstimator(diffuse, fun, thresholdGray, thresholdColor)
  cut = 3./(2^16 - 1);

  diffuse(diffuse < cut) = cut;
  logDiffuse = log(diffuse);

  responseOrig = fun(logDiffuse);
  responseGray = projectGray(responseOrig);
  responseColor = projectColor(responseOrig);
  normedResponseColor = sqrt(sum(responseColor.^2, 3));

  logDiffuseGrayscale = log(mean(diffuse, 3));
  responseGrayscale = fun(logDiffuseGrayscale);

  est = responseGrayscale .* ...
    double(normedResponseColor > thresholdColor ...
         | abs(responseGray(:, :, 1)) > thresholdGray);
end

function [I_x] = get_gradients_x(I)
  I_x = zeros(size(I));
  for i=1:size(I,3)
    for y=1:size(I,2)
      I_x(:, y, i) = I(:, mod(y, size(I, 2)) + 1, i) - I(:, y, i);
    end
  end
end

function [I_y] = get_gradients_y(I)
  I_y = zeros(size(I));
  for i=1:size(I,3)
    for x=1:size(I,1)
      I_y(x, :, i) = I(mod(x, size(I, 1)) + 1, :, i) - I(x, :, i);
    end
  end
end

function [p] = projectGray(e)
  p = repmat(mean(e, 3), [1, 1, 3]);
end

function [p] = projectColor(e)
  p = e - projectGray(e);
end
