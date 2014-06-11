function [reflectance shading] = IntrinsicImage_GS_Brush(g_name,wd,iterNum,rho,brush_YorN,R_Tag,S_Tag,L_Tag,MaxS,lamda)
%%%%%%%%求解线性方程组2
%%%%%%%%%三种画笔：
%<1>彩色画笔：画笔的R、G、B三个通道的值各不相同，用这类画笔来表示颜色一致区域，每种颜色的画笔代表一个颜色一致区域
%<2>灰度画笔；画笔的R、G、B三个通道的值成比例，用这类画笔来表示亮度一致区域，每种灰度的画笔代表一个亮度一致区域
%<3>红色画笔：画笔的R通道值为255，用这种画笔来表示亮度为1（也就是图像中最亮但又非高光的区域）
% rho = 1.9;%%松弛因子
% lamda = 0.5; %%画笔权重
% wd=3;                             %窗宽
% MaxS = 0.9 表示第三种画笔亮度指定画笔对应的亮度值

epsilon = 1/10000;

rgbIm=double(imread(g_name))/255 + epsilon;
ntscIm = rgb2ntsc(rgbIm);
n=size(ntscIm,1); m=size(ntscIm,2);
imgSize=n*m;


%%%%构造大小为imgSize*((2*wd+1)^2-1)的W矩阵
display('Compute Weight matrix');
tic

gvals=zeros(1,(2*wd+1)^2);                           %用于临时存贮某个窗内的像素权值，根据亮度Y来计算权重
t_cvals = zeros((2*wd+1)^2,3);                          %用于临时存贮某个窗内的像素点三元组，用于计算夹角

rgbIm2 = sum(rgbIm.^2,3);
rgbIm_c = rgbIm ./ (repmat(rgbIm2.^(1/2),[1 1 3]));        %将向量(r,g,b)单位化，

%%%%%%%每个像素的weight权值不一定有8个，在边界处的weight只有3个，
num_W = (2*wd+1)^2-1;                  
W = zeros(imgSize,num_W);
n_idx = ones(imgSize,num_W);
pixelIdx = reshape(1:imgSize,n,m);
  
len = 0;
for j=1:m
   for i=1:n
            len=len+1;
            tlen=0;            
            for ii=max(1,i-wd):min(i+wd,n)
                for jj=max(1,j-wd):min(j+wd,m)
                    if (ii~=i)||(jj~=j)
                        tlen=tlen+1;
                        gvals(tlen)=ntscIm(ii,jj,1); 
                        t_cvals(tlen,:) = reshape(rgbIm_c(ii,jj,:),1,3);                      
                        n_idx(len,tlen) = pixelIdx(ii,jj);
                    end
                end
            end
            
            %求窗内Y值的方差
            t_val=ntscIm(i,j,1);            
            gvals(tlen+1)=t_val;                    
            c_var=mean((gvals(1:tlen+1)-mean(gvals(1:tlen+1))).^2);                              %change                   
            csig=c_var*0.6;         
                      
            mgv=min((gvals(1:tlen)-t_val).^2);
            if (csig<(-mgv/log(0.01)))
                csig=-mgv/log(0.01);
            end
            if (csig<0.000002)
                csig=0.000002;
            end        
            
            %求窗内夹角的方差
            t_cval = reshape(rgbIm_c(i,j,:),1,3);        
            cvals = sum(t_cvals(1:tlen,:) .* repmat(t_cval,[tlen 1]),2);
            inds = cvals > 1;
            cvals(inds) = 1;
            cvals = acos(cvals);
            c_var_cvals = mean((cvals - mean(cvals)).^2); 
            csig_cvals = c_var_cvals*0.6;             
            mgv_cvals=min((cvals-1).^2);                              %change
            if (csig_cvals<(-mgv_cvals/log(0.01)))                              %change
                csig_cvals=-mgv_cvals/log(0.01);                              %change
            end                                                     %change
            if (csig_cvals<0.000002)                              %change
                csig_cvals=0.000002;                              %change
            end  

            gvals(1:tlen)=exp(-(((gvals(1:tlen)-t_val).^2/csig)+(cvals'.^2/ csig_cvals.^2)));
            tmp_sum = sum(gvals(1:tlen));
            gvals(1:tlen)=gvals(1:tlen)/tmp_sum;        
            
            W(len,1:tlen) = gvals(1:tlen); 
   end
end

if len ~= imgSize
    display('there are erros in creating the W matrix!');
    return;
end
toc
%%构造W矩阵


%%迭代
% R = 0.5*ones(n,m,3);
% inv_S = 2*ones(n,m);
R = 0.5*ones(imgSize,3);
inv_S = 2*ones(imgSize,1);
rgbIm = reshape(rgbIm,imgSize,3);
rgbIm2 = reshape(rgbIm2,imgSize,1);

for iter = 1:iterNum
iter
tic
    
%% 计算画笔约束
    if brush_YorN
        R_BrushNum = R_Tag{4};
        S_BrushNum = S_Tag{4};
        R_BrushR = zeros(R_BrushNum,3);
        S_BrushS = zeros(S_BrushNum,1);

        for b = 1:R_BrushNum
            for channel = 1:3
                R_BrushIndex = R_Tag{3}{b};
                [minValue index] = min(inv_S(R_BrushIndex));
                single_rgbIm = rgbIm(:,channel);
                sum2 = sum(single_rgbIm(R_BrushIndex(index))) / sum(1 ./ inv_S(R_BrushIndex(index)));
                R_BrushR(b,channel) = sum2;
            end
        end

        for b = 1:S_BrushNum
            S_BrushS(b) = sum(inv_S(S_Tag{3}{b})) / S_Tag{2}(b);
        end
    end
toc

%% 更新值
    sI = repmat(inv_S, [1 3]) .* rgbIm;
    len = 0;     
    for j = 1:m
       for i = 1:n
           len = len + 1;       
           sumR = W(len,:)*R(n_idx(len,:),:) + sI(len,:);
           R(len,:) = (1-rho)*R(len,:) + 0.5*rho*sumR;
           R(len,:) = max(epsilon, min(1, R(len,:)));
           
           if brush_YorN && iter ~= iterNum
              if R_Tag{1}(i,j)         
                   R(len,:) = ((1-lamda)*R(len,:) + lamda*R_BrushR(R_Tag{1}(i,j),:));
                   R(len,:) = max(epsilon, min(1, R(len,:)));
              end
           end
       end
    end
    
    inv_S = (1-rho)*inv_S + rho*(sum(rgbIm.*R,2)./rgbIm2);
    inv_S = max(1, inv_S);
    for j=1:m
       for i=1:n
           if brush_YorN && iter ~= iterNum
               len = pixelIdx(i,j);
               if S_Tag{1}(i,j)
                   inv_S(len) = ((1-lamda)*inv_S(len) + lamda*S_BrushS(S_Tag{1}(i,j))); 
                   inv_S(len) = max(1, inv_S(len));
                   R(len,:) = rgbIm(len,:) * inv_S(len);       
               else
                   if L_Tag{1}(i,j)
                       inv_S(len) = 1/MaxS;
                       R(len,:) = rgbIm(len,:) * inv_S(len);
                   end
               end
           end
       end
    end

toc
end

%%
reflectance = reshape(R, [n m 3]);
shading = reshape(1./inv_S, n, m);


