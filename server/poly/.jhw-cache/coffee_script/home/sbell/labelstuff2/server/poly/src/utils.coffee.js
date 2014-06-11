(function() {
  var clone_pt, mod, set_btn_enabled;

  set_btn_enabled = function(selector, enabled) {
    if (enabled == null) {
      enabled = true;
    }
    if (enabled) {
      return $(selector).removeAttr('disabled');
    } else {
      return $(selector).attr('disabled', 'disabled');
    }
  };

  mod = function(x, n) {
    return ((x % n) + n) % n;
  };

  clone_pt = function(o) {
    return {
      x: o.x,
      y: o.y
    };
  };

}).call(this);
