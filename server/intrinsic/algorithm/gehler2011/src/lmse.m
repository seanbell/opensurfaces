% sse = lmse(R,S,Rpred,Spred,window_size,mask)
%
% computes the local mean squared error (LMSE) as used in the paper
% "Ground Truth dataset and baseline evaluations for intrinsic image
% algorithms:" from Grosse et al. Eq. (7),(8) and (9)
%
% Is verified to produce the same result as the python implementation of
% Grosse. 
%
% Author: Peter Gehler (pgehler@vision.ee.ethz.ch)
% Date: 15 May 2010
function [sse,sse_r,sse_s,sseImage] = lmse(R,S,Rpred,Spred,window_size,mask);

    %assert(ndims(R)==3,'Reflectence input dim error');
    assert(ndims(S)==2,'Shading input dim error');
    assert(all(size(R)==size(Rpred)));
    assert(all(size(S)==size(Spred)));

    window_shift = window_size/2; 
    if ~exist('mask','var'), 
        mask = ones(size(S));
    end
    if ndims(R)==3
        R = mean(R,3);
        Rpred = mean(Rpred,3);
    end
    
    [sse_s, sseImage_s] = localErr(S,Spred,mask,window_size,window_shift);
    [sse_r, sseImage_r] = localErr(R,Rpred,mask,window_size,window_shift);

    sseImage = getNormalized(sseImage_s + sseImage_r);
    
    sse = 0.5 * (sse_r+sse_s);
    
    sse = sse;
    sse_r = sse_r;
    sse_s = sse_s;
    
function [ssq, ssqImage] = localErr(I,Ipred,mask,window_size, window_shift)
   ssqImage = zeros(size(I));

   if ndims(I)==3
        [m,n,d] = size(I);
        mask = repmat(mask,[1,1,3]);
    else
        [m,n] = size(I);
    end

    assert(~any(isnan(Ipred(mask==1))));
    
    ssq = 0;   total = 0;
    for i=0:window_shift:(m-window_shift-1)
        for j=0:window_shift:(n-window_shift-1)
            ind1 = i+(1:window_size);ind1(ind1>m)=[];
            ind2 = j+(1:window_size);ind2(ind2>n)=[];
            correct_curr = I(ind1,ind2,:);
            estimate_curr = Ipred(ind1,ind2,:);
            mask_curr = mask(ind1,ind2,:);
            [ssq_curr, ssqWindow] = ssqErr(correct_curr, estimate_curr, mask_curr);
            ssq = ssq + ssq_curr;
            ssqImage(ind1, ind2, :) = ssqImage(ind1, ind2, :) + ssqWindow;
            total = total + sum(vec(mask_curr .* correct_curr.^2));
        end
    end
    
    ssq = ssq/total;

function [ssq, ssqWindow] = ssqErr(correct, estimate, mask)

    assert(ndims(mask)==ndims(estimate),'input dim mismatch');
    assert(ndims(correct)==ndims(estimate),'input dim mismatch');
    assert(~any(isnan(estimate(mask==1))));

    if sum(vec(estimate.^2 .* mask)) > 1e-5
        alpha = sum(vec(correct .* estimate .* mask)) / sum(vec(estimate.^2 .*mask));
    else
        alpha = 0;
    end
    ssqWindow = mask.*(correct-alpha*estimate).^2;
    ssq = sum(vec(ssqWindow));
    assert(ssq>=0);
    
function a = vec(a)
    a = a(:);
