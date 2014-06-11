function [R_Tag S_Tag L_Tag] = ExtractBrushTag(Im_oringinal,Im_Brush)
%创建用于标注画笔种类的矩阵，同时存储每类画笔所覆盖的像素数目，R_Tag存储颜色一致性画笔，S_Tag存储亮度一致性画笔，L_Tag存储最大亮度画笔,
%Im_oringinal为原三通道图,Im_Brush为加了画笔后的图，像素取值范围是 0-255
height = size(Im_oringinal,1);
width = size(Im_oringinal,2);

R_Tag = cell(1,4);
R_Tag{1} = zeros(height,width);        %存储R画笔矩阵,有画笔的像素非零，并且这个非零数表示此类画笔的类别个数,类别总数存储在R_Tag{4}中
R_Tag{2} = [];                         %存储每类R画笔的像素个数
R_Tag{3} = [];                         %存储每类R画笔的所有像素所在的位置

S_Tag = cell(1,3);
S_Tag{1} = zeros(height,width);
S_Tag{2} = [];
S_Tag{3} = [];

L_Tag = cell(1,3);
L_Tag{1} = zeros(height,width);
L_Tag{2} = [];
L_Tag{3} = [];

[brushArray brush_Num] = ExtractColorBrushSub(Im_oringinal,Im_Brush);

R_class = 0;
S_class = 0;

for i = 1:brush_Num
    r = brushArray{i,3}(1);
    g = brushArray{i,3}(2);
    b = brushArray{i,3}(3);
    if r == 255 && g == 0 && b == 0
        for j = 1:brushArray{i,2}
            L_Tag{1}(brushArray{i,1}(j,1),brushArray{i,1}(j,2)) = 1;
        end
        L_Tag{2} = brushArray{i,2};
        L_Tag{3} = find(L_Tag{1} == 1);
    elseif r == g && g == b
        S_class = S_class + 1;
        for j = 1:brushArray{i,2}
            S_Tag{1}(brushArray{i,1}(j,1),brushArray{i,1}(j,2)) = S_class;
        end   
        S_Tag{2}(S_class) = brushArray{i,2};
        S_Tag{3}{S_class} = find(S_Tag{1} == S_class);
    else
        R_class = R_class + 1;
        for j = 1:brushArray{i,2}
            R_Tag{1}(brushArray{i,1}(j,1),brushArray{i,1}(j,2)) = R_class;
        end
        R_Tag{2}(R_class) = brushArray{i,2};
        R_Tag{3}{R_class} = find(R_Tag{1} == R_class);
    end
end

R_Tag{4} = size(R_Tag{2},2);
S_Tag{4} = size(S_Tag{2},2);
L_Tag{4} = size(L_Tag{2},2);
        


