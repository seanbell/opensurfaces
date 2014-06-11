(function() {
  var geom;

  geom = require('../../src/geometry.coffee');

  describe('AABB', function() {
    describe("#contains_pt", function() {
      return it("checks if it contains a point", function() {
        var bb, p;
        bb = new AABB();
        p = {
          x: 1,
          y: 2
        };
        bb.extend_pt(p);
        return expect(bb.contains_pt(p)).toEqual(true);
      });
    });
    describe("#intersects_bbox", function() {
      return it("checks if two bboxes intersect", function() {
        var bb1, bb2, bb3, max, min;
        bb1 = new AABB(min = {
          x: 0,
          y: 0
        }, max = {
          x: 2,
          y: 2
        });
        bb2 = new AABB(min = {
          x: 1,
          y: 1
        }, max = {
          x: 3,
          y: 3
        });
        expect(bb1.intersects_bbox(bb2)).toEqual(true);
        bb3 = new AABB(min = {
          x: 3,
          y: 3
        }, max = {
          x: 4,
          y: 4
        });
        return expect(bb1.intersects_bbox(bb3)).toEqual(false);
      });
    });
    describe("#contains_bbox", function() {
      return it("checks if a bbox entirely contains another", function() {
        var bb1, bb2, bb3, max, min;
        bb1 = new AABB(min = {
          x: 0,
          y: 0
        }, max = {
          x: 2,
          y: 2
        });
        bb2 = new AABB(min = {
          x: 1,
          y: 1
        }, max = {
          x: 3,
          y: 3
        });
        expect(bb1.contains_bbox(bb2)).toEqual(false);
        bb3 = new AABB(min = {
          x: 1,
          y: 1
        }, max = {
          x: 1.5,
          y: 1.5
        });
        return expect(bb1.contains_bbox(bb2)).toEqual(true);
      });
    });
    describe("#extend_pt", function() {
      return it("extends a bbox to contain a new point", function() {
        var bb, p;
        bb = new AABB();
        expect(bb.contains_pt(p)).toEqual(false);
        p = {
          x: 1,
          y: 2
        };
        bb.extend_pt(p);
        return expect(bb.contains_pt(p)).toEqual(true);
      });
    });
    return describe("#recompute_from_points", function() {
      return it("recomputes a new box to contain points", function() {
        var bb, p, p1, p2;
        bb = new AABB();
        expect(bb.contains_pt(p)).toEqual(false);
        p = {
          x: 1,
          y: 2
        };
        bb.extend_pt(p);
        expect(bb.contains_pt(p)).toEqual(true);
        p1 = {
          x: -2,
          y: -1
        };
        p2 = {
          x: 0,
          y: 0
        };
        bb.recompute_from_points([p1, p2]);
        expect(bb.contains_pt(p)).toEqual(false);
        expect(bb.contains_pt(p1)).toEqual(true);
        return expect(bb.contains_pt(p2)).toEqual(true);
      });
    });
  });

}).call(this);
