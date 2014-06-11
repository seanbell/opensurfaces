function self = ClusterTerm(img, parameter, opts, r)
  self = struct();

  self.k = parameter.k;
  self.kMeansRestarts = parameter.kMeansRestarts;

  self.normedDiffuse = img.normedDiffuse;

  self = initializeCluster(self, img, parameter, r);

  self = updateAlphaIdx(self);

  self.getEnergy = @getEnergy;
  self.update = @update;
  self.putStats = @putStats;

function [E, dE] = getEnergy(self, r)
  % compute variables depending on the input r
  estDiffuse = bsxfun(@times, self.normedDiffuse, r);

  clusterMean = computeClusterMean(self, estDiffuse);
  diff = estDiffuse-clusterMean(self.C, :);

  E = 1/3 * sum(diff(:).^2);
  dE = (2/3) * sum(self.normedDiffuse .* diff, 2);

function self = update(self, r)
  estDiffuse = bsxfun(@times, self.normedDiffuse, r);

  clusterMean = computeClusterMean(self, estDiffuse);
  self.C = mpi_assign_mex(estDiffuse',clusterMean');

  if numel(unique(self.C(:)))~=self.k
    h = hist(self.C, 1:self.k);
    clusterMean(h==0, :) = []; clusterMean(end+1:self.k, :) = 0;
    [RC, sse, self.C] = mpi_kmeans(estDiffuse', clusterMean', 0, ...
      self.kMeansRestarts);
  end

  self = updateAlphaIdx(self);

  assert(numel(unique(self.C(:)))==self.k, 'empty clusters');

function stats = putStats(self, stats)
  stats.C = self.C;
  stats.nClusters = numel(unique(self.C));

function clusterMean = callClusteringMethod(estDiffuse, k, restarts)
  clusterMean = mpi_kmeans(estDiffuse', k, 0, restarts);

function self = initializeCluster(self, img, parameter, r)
  estDiffuse = bsxfun(@times, self.normedDiffuse, r);

  switch parameter.clusteringInit
   case 'RhatR'
    clusterMean = callClusteringMethod(estDiffuse, parameter.k, ...
      parameter.kMeansRestarts);
    C = mpi_assign_mex(estDiffuse', clusterMean);

   case 'chromaticity'
    clusterMean = callClusteringMethod(img.normedDiffuse, self.k, opts);
    C = mpi_assign_mex(img.diffuse',RC);

   case 'normI'
    clusterMean = callClusteringMethod(img.norm, self.k, opts);
    C = mpi_assign_mex(img.norm',RC);

   otherwise
    error('unknown clusteringInit');
  end

  self.C = C;
  assert(self.k == numel(unique(self.C(:))));

function self = updateAlphaIdx(self)
  for i=1:max(self.C(:))
    self.alphaIndx{i} = find(self.C==i);
  end

function clusterMean = computeClusterMean(self, estDiffuse)
  clusterMean = zeros(max(self.C(:)),3);
  for i=1:max(self.C(:))
    if ~numel(self.alphaIndx{i}), continue; end
    clusterMean(i,:) = mean(estDiffuse(self.alphaIndx{i}, :), 1);
  end
