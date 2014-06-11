function [CX, sse, assignment] = mpi_kmeans(X, initcenters, maxiterations,nr_restarts, w)

% MPI_KMEANS    K-means clustering
%               [CX, sse] = mpi_kmeans(X, initcenters)
%	or	CX = mpi_kmeans(X, initcenters)
%       or      [CX, sse] = mpi_kmeans(X, initcenters,maxiterations)
%       or      [CX, sse] = mpi_kmeans(X, initcenters,maxiterations,nr_restarts)
%       or      [CX, sse] = mpi_kmeans(X, initcenters,maxiterations,nr_restarts,w)
%       or      [CX, sse, assignment] = mpi_kmeans(X, ... )
%
%               - X: [DxN] Matrix of N input points each is of D dimensions
%               - initcenters: 
%			either [1x1]: number of clusters (eg =10)
%			or [DxK] matrix of starting points
%		- maxiterations (=Inf): maximum number of iterations
%		- nr_restarts(=0): return the best result (lowest sse) over
%		nr_restart+1 independent runs of the K-kmeans algorithm 
%		- w: [Nx1] Vector with per sample weights
%
%               - CX: [DxK] matrix of cluster centers
%               - sse: Sum of Squared Error (faster if not
%               requested)
%		- assignment: [Nx1] vector of points X to nearest cluster center
%
% Example: 
%  X = randn(128,10000);
%   [Cx,sse] = mpi_kmeans(X,50);
%   [Cx,sse] = mpi_kmeans(X,randn(128,50));
%
% This code implements the algorithm presented in the ICML 2003
% paper "Using the Triangle Inequality to Accelerate K-Means" from
% Charles Elkan
%
% builds up on a previous version using the standard algorithm from
% Mark Everingham <me@robots.ox.ac.uk>
%
% Author: Peter Gehler <pgehler@tuebingen.mpg.de>
% Date: 12 Dec 07


if ~exist('nr_restarts','var')
    nr_restarts = 0;
end

if ~exist('maxiterations','var') || numel(maxiterations) == 0 || isinf(maxiterations)
    maxiterations = 0;
end
if ~exist('w','var')
    w = ones(size(X,2),1);
end

[CX,sse,assignment] = mpi_kmeans_mex(X,initcenters,maxiterations,nr_restarts,w);



nPopulatedCenters = numel(unique(assignment));
if numel(initcenters)==1, 
    K = initcenters;
else
    K = size(initcenters,2);
end

% there are fewer cluster centers than points
if (0)
if nPopulatedCenters < K
    nDisjointX = size(unique(fix(X'*10e10)/10e10,'rows'),1);
    assert(nDisjointX<=nPopulatedCenters);
    
    CX = unique(fix(CX'*10e10)/10e10,'rows');
    CX = CX';
    assignment = mpi_assign_mex(X,CX);
end
end


