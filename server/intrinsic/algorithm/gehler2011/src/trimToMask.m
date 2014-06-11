% B = trimToMask(A,mask)
% 
% retrieves A where mask>0
%
% input:
%	A - [m,n,d] matrix
%	mask - [m,n] matrix of [0,1]
%
% output:
%	B - [q,d] matrix where q==sum(mask(:)>0)
%
% inverted by 'insertIntoMask'
function A = trimToMask(A,mask)


[m,n] = size(mask);

if ndims(A)==2 & size(A,1) == sum(mask(:)==1);
    return;
end


if size(A,1)==m & size(A,2)==n
    [m,n,d] = size(A);
    A = reshape(A,[m*n,d]);
    mask = reshape(mask,[m*n,1]);
    A(find(mask==0),:) = [];
    return;
end

if ndims(A)==2 & size(A,1) == m*n
    [mn,d] = size(A);
    mask = reshape(mask,[m*n,1]);
    A(find(mask==0),:) = [];
    return;
end


assert(false,'invalid input to trimToMask');
