function [Lh,Lv] = create4connected_L1(m,n,mask);


if (0)
    % old an inefficient code

    mn=m*n;
    a = ones(mn,1);

    L = 4*speye(mn,mn) - spdiags(a,m,mn,mn) - spdiags(a,-m,mn,mn);
    L = L - spdiags(a,1,mn,mn) - spdiags(a,-1,mn,mn);

    rng = m:m:mn-1;
    L(rng,rng+1) = 0;
    L(rng+1,rng) = 0;
end

mn = m*n;
a = ones(mn,1);
rng = m:m:mn-1;

% remove boundary pixels
A = spdiags(a,1,mn,mn);
A(rng,rng+1) = 0;

B = spdiags(a,m,mn,mn);
B(rng+1,rng) = 0;


Lv = speye(mn) - A;
for i=m:m:mn
  Lv(i,i-1) = -0.5;
  Lv(i,i) = 0.5;
  
  Lv(i-1,i-1) = 0.5;
  Lv(i-1,i) = -0.5;
  
end


Lh = speye(mn) - B;
for i=m*(n-1)+1:mn
  Lh(i,i) = 0.5;
  Lh(i,i-m) = -0.5;
  
  Lh(i-m,i) = -0.5;
  Lh(i-m,i-m) = 0.5;
end



if exist('mask','var') && any(mask(:)==0)
    maskInd = find(mask(:)~=0);
    Lh = Lh(maskInd,maskInd);
    Lv = Lv(maskInd,maskInd);
end

assert(issparse(Lh));
assert(issparse(Lv));

%brute force implementation
% w=m;
% h=n;
% 
% WSIZE=3;
% WSIZE_2=1;
% 
% indsM=-ones(h+2,w+2);
% indsM(2:h+1,2:w+1)=reshape([1:h*w],h,w);
% 
% 
% len=0;
% tlen=(w)*(h)*9;
% row_inds=zeros(tlen ,1);
% col_inds=zeros(tlen ,1);
% vals=zeros(tlen,1);
% 
% 
% for y=1:h
%     for x =1:w
%         
%         
%         win_inds=indsM(y-WSIZE_2+1:y+WSIZE_2+1,x-WSIZE_2+1:x+WSIZE_2+1);
%         win_inds=win_inds(:);
%         num=0;
%         for i=[2 4 6 8]
%             if (win_inds(i)~=-1)
%                 
%                 len=len+1;
%                 vals(len)=-1;
%                 num=num+1;
%                 row_inds(len)=win_inds(i);
%                 col_inds(len)=win_inds(5);
%                 
%             end
%         end
%         len=len+1;
%         vals(len)=num;
%         row_inds(len)=win_inds(5);
%         col_inds(len)=win_inds(5);
%       end
% end
% vals=vals(1:len);
% row_inds=row_inds(1:len);
% col_inds=col_inds(1:len);
% 
% L=sparse(row_inds,col_inds,vals,w*h,w*h);
% 
% if exist('mask','var') && any(mask(:)==0)
%     maskInd = find(mask(:)==0);
%     L(maskInd,:) = [];
%     L(:,maskInd) = [];
% end
% assert(issparse(L));