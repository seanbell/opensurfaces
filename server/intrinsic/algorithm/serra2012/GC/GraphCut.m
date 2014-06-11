function [gch, varargout] = GraphCut(mode, varargin)
%
%   Performing Graph Cut energy minimization operations on a 2D grid.
%   
%   Usage:
%       [gch ...] = GraphCut(mode, ...);
%   
%
%   Inputs:
%   - mode: a string specifying mode of operation. See details below.
%
%   Output:
%   - gch: A handle to the constructed graph. Handle this handle with care
%          and don't forget to close it in the end!
%
%   Possible modes:
%   - 'open': Create a new graph object
%           [gch] = GraphCut('open', DataCost, SmoothnessCost);
%           [gch] = GraphCut('open', DataCost, SmoothnessCost, vC, hC);
%           [gch] = GraphCut('open', DataCost, SmoothnessCost, SparseSmoothness);
%
%       Inputs:
%           - DataCost a height by width by num_labels matrix where
%             Dc(r,c,l) equals the cost for assigning label l to pixel at (r,c)
%             Note that the graph dimensions, and the number of labels are deduced 
%             form the size of the DataCost matrix.
%             When using SparseSmoothness Dc is of (L)x(P) where L is the
%             number of labels and P is the number of nodes/pixels in the
%             graph.
%           - SmoothnessCost a #labels by #labels matrix where Sc(l1, l2)
%             is the cost of assigning neighboring pixels with label1 and
%             label2. This cost is spatialy invariant
%           - vC, hC:optional arrays defining spatialy varying smoothness cost. 
%                       Single precission arrays of size width*height.
%                       The smoothness cost is computed using:
%                       V_pq(l1, l2) = V(l1, l2) * w_pq
%                       where V is the SmoothnessCost matrix
%                       w_pq is spatialy varying parameter:
%                       if p=(r,c) and q=(r+1,c) then w_pq = vCue(r,c)
%                       if p=(r,c) and q=(r,c+1) then w_pq = hCue(r,c)
%                       (therefore in practice the last column of vC and
%                       the last row of vC are not used).
%           - SparseSmoothness: a sparse matrix defining both the graph
%               structure (might be other than grid) and the spatialy varying
%               smoothness term. Must be real positive sparse matrix of size
%               num_pixels by num_pixels, each non zero entry (i,j) defines a link
%               between pixels i and j with w_pq = SparseSmoothness(i,j).
%
%   - 'set': Set labels
%           [gch] = GraphCut('set', gch, labels)
%
%       Inputs:
%           - labels: a width by height array containing a label per pixel.
%             Array should be the same size of the grid with values
%             [0..num_labels].
%
%
%   - 'get': Get current labeling
%           [gch labels] = GraphCut('get', gch)
%
%       Outputs:
%           - labels: a height by width array, containing a label per pixel. 
%             note that labels values are in range [0..num_labels-1].
%
%
%   - 'energy': Get current values of energy terms
%           [gch se de] = GraphCut('energy', gch)
%           [gch e] = GraphGut('energy', gch)
%
%       Outputs:
%           - se: Smoothness energy term.
%           - de: Data energy term.
%           - e = se + de
%
%
%   - 'expand': Perform labels expansion
%           [gch labels] = GraphCut('expand', gch)
%           [gch labels] = GraphCut('expand', gch, iter)
%           [gch labels] = GraphCut('expand', gch, [], label)
%           [gch labels] = GraphCut('expand', gch, [], label, indices)
%
%       When no inputs are provided, GraphCut performs expansion steps
%       until it converges.
%
%       Inputs:
%           - iter: a double scalar, the maximum number of expand
%                    iterations to perform.
%           - label: scalar denoting the label for which to perfom
%                     expand step (labels are [0..num_labels-1]).
%           - indices: array of linear indices of pixels for which
%                        expand step is computed. 
%
%       Outputs:
%           - labels: a width*height array of type int32, containing a
%              label per pixel. note that labels values must be is range
%              [0..num_labels-1].
%
%
%   - 'swap': Perform alpha - beta swappings
%           [gch labels] = GraphCut('swap', gch)
%           [gch labels] = GraphCut('swap', gch, iter)
%           [gch labels] = GraphCut('swap', gch, label1, label2)
%
%       When no inputs are provided, GraphCut performs alpha - beta swaps steps
%       until it converges.
%
%       Inputs:
%           - iter: a double scalar, the maximum number of swap
%                      iterations to perform.
%           - label1, label2: int32 scalars denoting two labels for swap
%                                       step.
%
%       Outputs:
%           - labels: a width*height array of type int32, containing a
%              label per pixel. note that labels values must be is range
%              [0..num_labels-1].
%
%
%   - 'close': Close the graph and release allocated resources.
%       [gch] = GraphCut(gch,'close');
%
%
%
%   This wrapper for Matlab was written by Shai Bagon (shai.bagon@weizmann.ac.il).
%   Department of Computer Science and Applied Mathmatics
%   Wiezmann Institute of Science
%   http://www.wisdom.weizmann.ac.il/
%
%	The core cpp application was written by Olga Veksler
%	(available from http://www.csd.uwo.ca/faculty/olga/code.html):
%
%   [1] Efficient Approximate Energy Minimization via Graph Cuts
%        Yuri Boykov, Olga Veksler, Ramin Zabih,
%        IEEE transactions on PAMI, vol. 20, no. 12, p. 1222-1239, November
%        2001.
% 
%   [2] What Energy Functions can be Minimized via Graph Cuts?
%        Vladimir Kolmogorov and Ramin Zabih.
%        IEEE Transactions on Pattern Analysis and Machine Intelligence
%        (PAMI), vol. 26, no. 2,
%        February 2004, pp. 147-159.
% 
%   [3] An Experimental Comparison of Min-Cut/Max-Flow Algorithms
%        for Energy Minimization in Vision.
%        Yuri Boykov and Vladimir Kolmogorov.
%        In IEEE Transactions on Pattern Analysis and Machine Intelligence
%        (PAMI),
%        vol. 26, no. 9, September 2004, pp. 1124-1137.
% 
%   [4] Matlab Wrapper for Graph Cut.
%        Shai Bagon.
%        in www.wisdom.weizmann.ac.il/~bagon, December 2006.
% 
%   This software can be used only for research purposes, you should  cite ALL of
%   the aforementioned papers in any resulting publication.
%   If you wish to use this software (or the algorithms described in the
%   aforementioned paper)
%   for commercial purposes, you should be aware that there is a US patent:
%
%       R. Zabih, Y. Boykov, O. Veksler,
%       "System and method for fast approximate energy minimization via
%       graph cuts ",
%       United Stated Patent 6,744,923, June 1, 2004
%
%
%   The Software is provided "as is", without warranty of any kind.
%
%

switch lower(mode)
    case {'o', 'open'}
        % open a new graph cut
        if nargout ~= 1
            error('GraphCut:Open: wrong number of output arguments');
        end

        gch = OpenGraph(varargin{:});

    case {'c', 'close'}
        % close the GraphCut handle - free memory.
        if nargin ~= 2
            error('GraphCut:Close: Too many inputs');
        end
        gch = varargin{1};
        [gch] = GraphCutMex(gch, 'c');
        
    case {'g', 'get'}
        % get current labeling
        
        if nargout ~= 2
            error('GraphCut:GetLabels: wrong number of outputs');
        end
        [gch labels] = GetLabels(varargin{:});

        varargout{1} = labels;
        
    case {'s', 'set'}
        % set user defined labeling
        if nargout ~= 1
            error('GraphCut:SetLabels: Too many outputs');
        end
        
        [gch] = SetLabels(varargin{:});
        
    case {'en', 'n', 'energy'}
        % get current energy values
        if nargin ~= 2
            error('GraphCut:GetEnergy: too many input arguments');
        end
        gch = varargin{1};
        [gch se de] = GraphCutMex(gch, 'n');
        switch nargout
            case 2
                varargout{1} = se+de;
            case 3
                varargout{1} = se;
                varargout{2} = de;
            case 1
            otherwise
                error('GraphCut:GetEnergy: wrong number of output arguments')
        end
   
    
    case {'e', 'ex', 'expand'}
        % use expand steps to minimize energy
        if nargout > 2
            error('GraphCut:Expand: too many output arguments');
        end
        [gch labels] = Expand(varargin{:});
        if nargout == 2
            varargout{1} = labels;
        end
        
    case {'sw', 'a', 'ab', 'swap'}
        % use alpha beta swapping to minimize energy
        if nargout > 2
            error('GraphCut:Expand: too many output arguments');
        end
        [gch labels] = Swap(varargin{:});
        if nargout == 2
            varargout{1} = labels;
        end
        
    otherwise
        error('GraphCut: Unrecognized mode %s', mode);
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%   Aux functions
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function gch = OpenGraph(varargin)
% Usage [gch] = OpenGraph(Dc, Sc, [vC, hC]) - 2D grid
% or    [gch] = OpenGraph(Dc, Sc, [Contrast]) -3D grid
% or    [gch] = GraphCut('open', DataCost, SmoothnessCost, SparseSmoothness) - any graph
nin = numel(varargin);
if (nin~=2)  && (nin ~= 3) && (nin~=4) 
    error('GraphCut:Open: wrong number of inputs');
end

% Data cost
Dc = varargin{1};
if ndims(Dc) == 4
    %% 3D graph
    [R C Z L] = size(Dc);
    if ~strcmp(class(Dc),'single')
        Dc = single(Dc);
    end
    Dc = permute(Dc,[4 1 2 3]);
    Dc = Dc(:)';
    
    % smoothness cost
    Sc = varargin{2};
    if any( size(Sc) ~= [L L] )
        error('GraphCut:Open: smoothness cost has incorrect size');
    end
    if ~strcmp(class(Sc),'single')
        Sc = single(Sc);
    end
    Sc = Sc(:)';
    if nin == 3
        Contrast = varargin{3};
        if any( size(Contrast) ~= [R C Z] )
            error('GraphCut:Open: Contrast term is of wrong size');
        end
        if ~strcmp(class(Contrast),'single')
            Contrast = single(Contrast);
        end
        Contrast = Contrast(:);
        
        gch = GraphCut3dConstr(R, C, Z, L, Dc, Sc, Contrast);
    else
        gch = GraphCut3dConstr(R, C, Z, L, Dc, Sc);
    end
elseif ndims(Dc) == 3
    %% 2D graph
    [h w l] = size(Dc);
    if ~strcmp(class(Dc),'single')
        Dc = single(Dc);
    end
    Dc = permute(Dc,[3 2 1]);
    Dc = Dc(:)';

    % smoothness cost
    Sc = varargin{2};
    if any( size(Sc) ~= [l l] )
        error('GraphCut:Open: smoothness cost has incorrect size');
    end
    if ~strcmp(class(Sc),'single')
        Sc = single(Sc);
    end
    Sc = Sc(:)';

    if nin==4
        vC = varargin{3};
        if any( size(vC) ~= [h w] )
            error('GraphCut:Open: vertical cue size incorrect');
        end
        if ~strcmp(class(vC),'single')
            vC = single(vC);
        end
        vC = vC';

        hC = varargin{4};
        if any( size(hC) ~= [h w] )
            error('GraphCut:Open: horizontal cue size incorrect');
        end
        if ~strcmp(class(hC),'single')
            hC = single(hC);
        end
        hC = hC';
        gch = GraphCutConstr(w, h, l, Dc, Sc, vC(:), hC(:));
    else
        gch = GraphCutConstr(w, h, l, Dc, Sc);
    end
elseif ndims(Dc) == 2
    %% arbitrary graph
    if nin ~= 3
        error('GraphCut:Open', 'incorect number of inputs');
    end
    
    [nl np] = size(Dc);
    Sc = varargin{2};
    if any(size(Sc) ~= [nl nl])
        error('GraphCut:Open', 'Wrong size of Dc or Sc');
    end
    
    SparseSc = varargin{3};
    if any(size(SparseSc) ~= [np np])
        error('GraphCut:Open', 'Wrong size of SparseSc');
    end
        
    gch = GraphCutConstrSparse(single(Dc(:)), single(Sc(:)), SparseSc);
        
else
    %% Unknown dimensionality...
    error('GraphCut:Open: data cost has incorect dimensionality');
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function [gch] = SetLabels(varargin)
% usgae [gch] = SetLabels(gch, labels)

if nargin ~= 2
    error('GraphCut:SetLabels: wrong number of inputs');
end
gch = varargin{1};
labels = varargin{2};

if ~strcmp(class(labels), 'int32')
    labels = int32(labels);
end
labels = labels';
[gch] = GraphCutMex(gch, 's', labels(:));

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function [gch labels] = GetLabels(varargin)

if nargin ~= 1
    error('GraphCut:GetLabels: wrong number of inputs');
end
gch = varargin{1};
[gch labels] = GraphCutMex(gch, 'g');
labels = labels';

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function [gch labels] = Expand(varargin)
gch = varargin{1};
switch nargin
    case 1
        [gch labels] = GraphCutMex(gch, 'e');
    case 2
        [gch labels] = GraphCutMex(gch, 'e', varargin{2});
    case 3
        [gch labels] = GraphCutMex(gch, 'e', varargin{2}, varargin{3});
    case 4
        ind = varargin{4};
        ind = int32(ind(:)-1)'; % convert to int32
        [gch labels] = GraphCutMex(gch, 'e', varargin{2}, varargin{3}, ind);
    otherwise
        error('GraphCut:Expand: wrong number of inputs');
end
labels = labels';

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function [gch labels] = Swap(varargin)
gch = varargin{1};
switch nargin
    case 1
        [gch labels] = GraphCutMex(gch, 'a');
    case 2
        [gch labels] = GraphCutMex(gch, 'a', varargin{2});
    case 3
        [gch labels] = GraphCutMex(gch, 'a', varargin{2}, varargin{3});
    otherwise
        error('GraphCut:Swap: wrong number of inputarguments');
end
labels = labels';

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
