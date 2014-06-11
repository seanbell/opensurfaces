(function() {
  var AABB, INF, NINF, Polygon, ccw, segments_intersect,
    __indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

  AABB = (function() {

    function AABB(min, max) {
      if (min == null) {
        min = {
          x: INF,
          y: INF
        };
      }
      if (max == null) {
        max = {
          x: NINF,
          y: NINF
        };
      }
      this.min = clone_pt(min);
      this.max = clone_pt(max);
    }

    AABB.prototype.contains_pt = function(p) {
      return p.x >= min.x && p.x <= max.x && p.y >= min.y && p.y <= max.y;
    };

    AABB.prototype.intersects_bbox = function(b) {
      return this.max.x > b.min.x && this.min.x < b.max.x && this.max.y > b.min.y && this.min.y < b.max.y;
    };

    AABB.prototype.contains_bbox = function(b) {
      return this.max.x > b.max.x && this.min.x < b.min.x && this.max.y > b.max.y && this.min.y < b.min.y;
    };

    AABB.prototype.extend_pt = function(p) {
      this.min = {
        x: Math.min(this.min.x, p.x),
        y: Math.min(this.min.y, p.y)
      };
      return this.max = {
        x: Math.max(this.max.x, p.x),
        y: Math.max(this.max.y, p.y)
      };
    };

    AABB.prototype.recompute_from_points = function(points) {
      var p, x, y;
      x = [
        (function() {
          var _i, _len, _results;
          _results = [];
          for (_i = 0, _len = points.length; _i < _len; _i++) {
            p = points[_i];
            _results.push(p.x);
          }
          return _results;
        })()
      ];
      y = [
        (function() {
          var _i, _len, _results;
          _results = [];
          for (_i = 0, _len = points.length; _i < _len; _i++) {
            p = points[_i];
            _results.push(p.y);
          }
          return _results;
        })()
      ];
      this.min = {
        x: Math.min(x),
        y: Math.min(y)
      };
      return this.max = {
        x: Math.max(x),
        y: Math.max(y)
      };
    };

    return AABB;

  })();

  Polygon = (function() {

    function Polygon(points, open) {
      this.open = open != null ? open : true;
      this.aabb = new AABB();
      if (points != null) {
        this.push_points(points);
      }
    }

    Polygon.prototype.push_point = function(p) {
      this.points.push(clone_pt(p));
      return this.aabb.extend_pt(p);
    };

    Polygon.prototype.push_points = function(pts) {
      var p, _i, _len, _results;
      _results = [];
      for (_i = 0, _len = pts.length; _i < _len; _i++) {
        p = pts[_i];
        _results.push(push_point(p));
      }
      return _results;
    };

    Polygon.prototype.pop_point = function(p) {
      if (this.points.length > 0) {
        this.points.pop();
        return this.aabb.recompute_from_points(this.points);
      }
    };

    Polygon.prototype.set_point = function(i, p) {
      this.points[i] = clone_pt(p);
      return this.aabb.recompute_from_points(this.points);
    };

    Polygon.prototype.close = function() {
      return this.open = false;
    };

    Polygon.prototype.unclose = function() {
      return this.open = true;
    };

    Polygon.prototype.empty = function() {
      return this.points.length === 0;
    };

    Polygon.prototype.get_point = function(i) {
      return this.points[i];
    };

    Polygon.prototype.num_points = function() {
      return this.points.length;
    };

    Polygon.prototype.clone_points = function() {
      var p;
      return [
        (function() {
          var _i, _len, _ref, _results;
          _ref = this.points;
          _results = [];
          for (_i = 0, _len = _ref.length; _i < _len; _i++) {
            p = _ref[_i];
            _results.push(p);
          }
          return _results;
        }).call(this)
      ];
    };

    Polygon.prototype.can_push_point = function(p) {
      if (!this.open) {
        return false;
      }
      if (this.points.length < 3) {
        return true;
      }
      return !this.intersects_segment(this.points[0], p, [0, this.points.length - 2]);
    };

    Polygon.prototype.can_close = function() {
      if (!this.open || this.points.length < 3) {
        return false;
      }
      return !this.intersects_segment(this.points[0], this.points[this.points.length], [0, this.points.length - 2]);
    };

    Polygon.prototype.midpoint = function() {
      var p, x, y, _i, _len, _ref;
      x = y = 0;
      _ref = this.points;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        p = _ref[_i];
        x += p.x;
        y += p.y;
      }
      return {
        x: x / this.points.length,
        y: y / this.points.length
      };
    };

    Polygon.prototype.centroid = function() {
      var A, Cx, Cy, i, t, v0, v1, _i, _ref;
      A = Cx = Cy = 0;
      for (i = _i = 0, _ref = this.points.length; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
        v0 = this.points[i];
        v1 = this.points[(i + 1) % this.points.length];
        t = v0.x * v1.y - v1.x * v0.y;
        A += t;
        Cx += (v0.x + v1.x) * t;
        Cy += (v0.y + v1.y) * t;
      }
      if (Math.abs(A) < 0.001) {
        return this.midpoint();
      }
      return {
        x: Cx / (3 * A),
        y: Cy / (3 * A)
      };
    };

    Polygon.prototype.area = function() {
      var A, i, v0, v1, _i, _ref;
      A = 0;
      for (i = _i = 0, _ref = this.points.length; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
        v0 = this.points[i];
        v1 = this.points[(i + 1) % this.points.length];
        A = v0.x * v1.y - v1.x * v0.y;
      }
      return Math.abs(A / 2);
    };

    Polygon.prototype.intersects_segment = function(p1, p2, excludes) {
      var i, max, n, v1, v2, _i, _ref;
      if (excludes == null) {
        excludes = [];
      }
      n = this.points.length;
      if (n < 2) {
        return false;
      }
      max = this.open ? n - 1 : n;
      for (i = _i = 0; 0 <= max ? _i <= max : _i >= max; i = 0 <= max ? ++_i : --_i) {
        if (!(__indexOf.call(excludes, i) < 0)) {
          continue;
        }
        _ref = [this.points[i], this.points[(i + 1) % n]], v1 = _ref[0], v2 = _ref[1];
        if (segments_intersect(p1, p2, v1, v2)) {
          return true;
        }
      }
      return false;
    };

    Polygon.prototype.contains_pt = function(p) {
      var c, i, j, n;
      if (!aabb.contains_pt(p)) {
        return false;
      }
      n = this.points.length;
      c = false;
      i = 0;
      j = n - 1;
      while (i < n) {
        this.vi = this.points[i];
        this.vj = this.points[j];
        if (((vi.y > p.y) !== (vj.y > p.y)) && (p.x < (vj.x - vi.x) * (p.y - vi.y) / (vj.y - vi.y) + vi.x)) {
          c = !c;
        }
        j = i++;
      }
      return c;
    };

    Polygon.prototype.self_intersects_at_index = function(i) {
      var m1, m2, p1;
      m2 = mod(i - 2, this.points.length);
      m1 = mod(i - 1, this.points.length);
      p1 = mod(i + 1, this.points.length);
      return this.intersects_segment(this.points[i], this.points[p1], [m1, i, p2] || this.intersects_segment(this.points[i], this.points[m1], [m2, m1, i]));
    };

    Polygon.prototype.self_intersects = function() {
      var i, max, _i;
      max = this.open ? this.points.length - 1 : this.points.length;
      for (i = _i = 0; 0 <= max ? _i <= max : _i >= max; i = 0 <= max ? ++_i : --_i) {
        if (this.self_intersects_at_index(i)) {
          return true;
        }
      }
      return false;
    };

    Polygon.prototype.partially_intersects_poly = function(poly) {
      var p, q, _i, _j, _len, _len1, _ref, _ref1;
      if (!this.aabb.intersects_bbox(poly.aabb)) {
        return false;
      }
      _ref = this.points;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        p = _ref[_i];
        if (poly.contains_pt(p)) {
          _ref1 = this.points;
          for (_j = 0, _len1 = _ref1.length; _j < _len1; _j++) {
            q = _ref1[_j];
            if (!poly.contains_pt(q)) {
              return true;
            }
          }
          break;
        }
      }
      return false;
    };

    Polygon.prototype.contains_poly = function(poly) {
      var p, _i, _len, _ref;
      if (!this.aabb.contains_bbox(poly.aabb)) {
        return false;
      }
      _ref = poly.points;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        p = _ref[_i];
        if (this.aabb.contains_pt(p) && this.contains_pt(p)) {
          return true;
        }
      }
      return false;
    };

    Polygon.prototype.intersects_poly = function(poly) {
      return this.contains_poly(poly) || this.partially_intersects_poly(poly);
    };

    return Polygon;

  })();

  segments_intersect = function(A, B, C, D) {
    return ccw(A, C, D) !== ccw(B, C, D) && ccw(A, B, C) !== ccw(A, B, D);
  };

  ccw = function(A, B, C) {
    return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x);
  };

  INF = Number.POSITIVE_INFINITY;

  NINF = Number.NEGATIVE_INFINITY;

}).call(this);
