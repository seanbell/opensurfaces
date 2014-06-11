function sub = index2sub(index,height)
%change the index column of the matrix to the subscript

sub = zeros(size(index,1),2);
for i = 1:size(index,1)
    row = rem(index(i),height);
    if row == 0
        row = height;
    end
    column = ceil(index(i) / height);
    sub(i,1) = row;
    sub(i,2) = column;
end
    