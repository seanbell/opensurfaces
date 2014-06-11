function x = getNormalized(x)
  max_ = max(x(:));
  min_ = min(x(:));

  x = (x-min_) / (max_ - min_);
end
