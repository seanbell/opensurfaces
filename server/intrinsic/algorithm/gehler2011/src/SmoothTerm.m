function self = SmoothTerm(img, opts)
  self = struct();

  self.laplacian = opts.laplacian;
  self.norm = img.norm;

  self.getEnergy = @getEnergy;
  self.update = @update;
  self.putStats = @putStats;

function [E, dE] = getEnergy(self, r)
  s = self.norm./r;
  normedDiffuseR2 = self.norm./(eps+r.^2);

  lS = self.laplacian*s;
  E = s'*lS;
  dE = -2 * (lS .* normedDiffuseR2);

function self = update(self, R)

function stats = putStats(self, stats)
