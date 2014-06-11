clear all


%
% Try some function calls
% 
try
    mpi_assign_mex(randn(10,100),randn(20,10));
    error('Dimension mismatch!');
end

try
    [CX1,sse,s] = mpi_kmeans_mex(randn(10,100), 0,0);    
    error('0 clusters');
end

%
% a very easy test with known outcome
%
X = [2 0 0;
     1 0 0;
     0 0 2;
     0 0 1;
     0 0 3];

[CX1,sse,s] = mpi_kmeans_mex(X',2,0,1000);


targetCX = [0 1.5;
	    0 0;
	    2 0];

d1 = sum(sum(abs(targetCX - CX1)));
d2 = sum(sum(abs(targetCX(:,2:-1:1) - CX1)));

assert(min(d1,d2)<1e-8);


%test weighting
try
    [CX1,sse,s] = mpi_kmeans_mex(X',2,0,1000);    
    error('weight vector mismatch');
end
W = ones(size(X,1),1);
[CX2,sse2,s2] = mpi_kmeans_mex(X',2,0,1000,W);

d1 = sum(sum(abs(targetCX - CX2)));
d2 = sum(sum(abs(targetCX(:,2:-1:1) - CX2)));

assert(min(d1,d2)<1e-8);


%test weighting
[CX1,sse1,s1] = mpi_kmeans_mex([X;X(1,:)]',2,0,1000);
[CX2,sse2,s2] = mpi_kmeans_mex(X',2,0,1000,[2,1,1,1,1]');

d1 = sum(sum(abs(CX1 - CX2)));
d2 = sum(sum(abs(CX1(:,2:-1:1) - CX2)));

assert(min(d1,d2)<1e-8);
assert(s1(1)==s1(end));


%
% do 100 random tests
%
for i=1:100
    
    if i==1
	dims = 1;
    else
	dims = ceil(80 * rand);
    end
    
    nclusts = i;
    npts = ceil(10000 * rand);
    X = randn(dims,npts);
    nr_restarts = round(3*rand);
    if nclusts == 1
	CX0 = 1;
    else
	CX0 = randn(dims,nclusts);
    end
    
    maxiter = 0;

    XX = X;
    CC = CX0;
    
    t=cputime;
    [CX1,sse,s] = mpi_kmeans_mex(X, CX0,maxiter,nr_restarts);    
    fprintf('%d: time needed %g\n',i,cputime-t);

    %t=cputime;
    %[ttCX1,ttsse,tts] = mpi_kmeans_mex(X, nclusts,maxiter,nr_restarts);    
    %fprintf('%d: time needed %g\n',i,cputime-t);
    %sse - ttsse
    
    assert((sum(XX(:)-X(:)))==0,'Training points X changed');
    assert((sum(CC(:)-CX0(:)))==0,'CX0 changed');
    assert(~any(isnan(CX1(:))),'NaN in CX1');
    
    s2 = mpi_assign_mex(X,CX1);
    assert(all(s2==s),'wrong assignment');

    clear centr
    if dims == 1
	for i=1:size(X,2)
	    [ignore,centr(i,1)] = min(( (CX1 - repmat(X(:,i),1,nclusts)).^2));
	end
    else
	for i=1:size(X,2)
	    [ignore,centr(i,1)] = min(sum( (CX1 - repmat(X(:,i),1,nclusts)).^2));
	end
    end
    
    assert(sum(abs([centr-double(s)]))==0,'wrong assignment');

    
    if (0)
	t=cputime;
	[CX2,sse2,s2] = mpi_kmeans_ordinary(X, CX0,maxiter);    
	fprintf('2: time needed %g\n',cputime-t);
	
	if (sum(XX(:)-X(:)))~=0
	    error('X changed\n');
	end
	if (sum(CC(:)-CX0(:)))~=0
	    error('CX changed\n');
	end

	if any(isnan(CX2(:))) 
	    error('CX2 isnan');
	end

	if (sum(sum(abs(CX1-CX2)))) > 1e-9
	    sum(sum(abs(CX1-CX2)))
	    error('bug: cluster centers not the same');
	end
	
	if (sum(s-s2))~=0
	    error('assignment not the same');
	end
	
	if abs(sse-sse2) > 1e-8
	    error('sse not the same');
	end
	

    end
    
end

fprintf('Test passed\n');
