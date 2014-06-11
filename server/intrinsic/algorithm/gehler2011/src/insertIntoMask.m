% B = insertIntoMask(A,mask)
%
% creates image with A where mask>0
%
% input
%	A - [q,d] matrix
%	mask - [m,n] matrix
% output
%	B - [m,n,d] matrix 
%
% inverts the operation 'trimToMask'
function B = insertIntoMask(A,mask)

[m,n,d] = size(mask);
assert(d==1);

if all([size(A,1),size(A,2)] == [m,n])
    B = A;
    return;
end

if ndims(A)==3
    assert(size(A,1)==m & size(A,2)==n,'invalid input to insertIntoMask');
    return;
end

B = zeros([m*n,size(A,2)]);
mask = reshape(mask,[m*n,1]);
maskInd = find(mask==1);

if size(A,1) == m*n
    B(maskInd,:) = A(maskInd,:);
elseif size(A,1) == sum(mask(:)==1)
    B(maskInd,:) = A;
else
    error('invalid input to insertIntoMask');
end

B = reshape(B,[m,n,size(B,2)]);