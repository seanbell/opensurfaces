function init_libs()

  folder = fileparts(which(mfilename));

  addpath([folder filesep 'minimize']);
  addpath([folder filesep 'mpi_kmeans-1.6']);
