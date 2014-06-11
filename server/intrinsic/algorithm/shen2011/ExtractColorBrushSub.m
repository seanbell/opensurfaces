function [brushArray brush_Num] = ExtractColorBrushSub(Im_oringinal,Brush)

% Extract the brush subscript from a 3 chanel color image

index = find(Im_oringinal(:,:,1) ~= Brush(:,:,1) | Im_oringinal(:,:,2) ~= Brush(:,:,2) | Im_oringinal(:,:,3) ~= Brush(:,:,3));

brush1 = Brush(:,:,1);
brush2 = Brush(:,:,2);
brush3 = Brush(:,:,3);

brush10 = 0*brush1;
brush20 = 0*brush2;
brush30 = 0*brush3;

brush10(index) = brush1(index);
brush20(index) = brush2(index);
brush30(index) = brush3(index);

% im(:,:,1) = brush10;
% im(:,:,2) = brush20;
% im(:,:,3) = brush30;
% 
% figure,imshow(im);

clear brush1 brush2 brush3 index

brush_color = [];
for i = 1:size(Im_oringinal,1)
    for j = 1:size(Im_oringinal,2)
        if brush10(i,j) ~= 0 ||  brush20(i,j) ~= 0 || brush30(i,j) ~= 0
            tag = 0;
            for k = 1:size(brush_color,1)
                if brush10(i,j) == brush_color(k,1) && brush20(i,j) == brush_color(k,2) && brush30(i,j) == brush_color(k,3)
                    tag = 1;
                    break;
                end
            end
            if tag == 0
                brush_color = [brush_color;[brush10(i,j) brush20(i,j) brush30(i,j)]];
            end
        end
    end
end

brush_Num = size(brush_color,1);
brushArray = cell(brush_Num,3);
for i = 1:brush_Num
    brushArray{i,1} = find(brush10 == brush_color(i,1) & brush20 == brush_color(i,2) & brush30 == brush_color(i,3));
    brushArray{i,1} = index2sub(brushArray{i,1},size(Im_oringinal,1));
    brushArray{i,2} = size(brushArray{i,1},1);
    brushArray{i,3} = brush_color(i,:);
end


