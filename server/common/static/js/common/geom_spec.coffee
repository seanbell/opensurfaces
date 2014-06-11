describe 'Point', ->

  it "should contain its constructor arguments", ->
    p = new Point(1, 2)
    expect(p.x).toEqual 1
    expect(p.y).toEqual 2

describe 'AABB', ->

  describe "#reset", ->

    beforeEach ->
      @bb = new AABB()
      @p = {x:1, y: 2}
      @p2 = {x:1, y: 2}

    it "should contain nothing", ->
      @bb.recompute_from_points([@p, @p2])
      @bb.reset()
      expect(@bb.contains_pt(@p)).toBe false
      expect(@bb.contains_pt(@p2)).toBe false

  describe "#contains_pt", ->

    beforeEach ->
      @bb = new AABB()
      @p = {x:1, y: 2}
      @p2 = {x:1, y: 2}

    it "should contain nothing when new", ->
      expect(@bb.contains_pt(@p)).toBe false

    it "should return true properly", ->
      @bb.extend_pt(@p)
      expect(@bb.contains_pt(@p)).toBe true

    it "should return false properly", ->
      @bb.extend_pt(@p)
      expect(@bb.contains_pt(@p2)).toBe true

  describe "#intersects_bbox", ->

    beforeEach ->
      @bb1 = new AABB({x:0,y:0}, {x:2,y:2})
      @bb2 = new AABB({x:1,y:1}, {x:3,y:3})
      @bb3 = new AABB({x:3,y:3}, {x:4,y:4})
      @bb4 = new AABB({x:0,y:0}, {x:1,y:1})
      @bb5 = new AABB({x:-1,y:0.2}, {x:2,y:0.8})

    it "should intersect itself", ->
      expect(@bb1.intersects_bbox(@bb1)).toBe true
      expect(@bb2.intersects_bbox(@bb2)).toBe true
      expect(@bb3.intersects_bbox(@bb3)).toBe true

    it "should not intersect a new box", ->
      expect(@bb1.intersects_bbox(new AABB())).toBe false

    it "should return true properly", ->
      expect(@bb1.intersects_bbox(@bb2)).toBe true
      expect(@bb2.intersects_bbox(@bb1)).toBe true
      expect(@bb4.intersects_bbox(@bb5)).toBe true
      expect(@bb5.intersects_bbox(@bb4)).toBe true

    it "should return false properly", ->
      expect(@bb1.intersects_bbox(@bb3)).toBe false
      expect(@bb3.intersects_bbox(@bb1)).toBe false

  describe "#contains_bbox", ->

    beforeEach ->
      @bb1 = new AABB({x:0,y:0}, {x:2,y:2})
      @bb2 = new AABB({x:1,y:1}, {x:3,y:3})
      @bb3 = new AABB({x:1,y:1}, {x:1.5,y:1.5})

    it "should contain itself", ->
      expect(@bb1.contains_bbox(@bb1)).toBe true
      expect(@bb2.contains_bbox(@bb2)).toBe true
      expect(@bb3.contains_bbox(@bb3)).toBe true

    it "should not return true for just intersection", ->
      expect(@bb1.contains_bbox(@bb2)).toBe false

    it "checks if a bbox entirely contains another", ->
      expect(@bb1.contains_bbox(@bb3)).toBe true
      expect(@bb3.contains_bbox(@bb1)).toBe false

  describe "#extend_pt", ->

    beforeEach ->
      @bb = new AABB()
      @p = {x:1, y: 2}

    it "should not contain the point before extending", ->
      expect(@bb.contains_pt(@p)).toBe false

    it "should contain the point after extending", ->
      @bb.extend_pt(@p)
      expect(@bb.contains_pt(@p)).toBe true

    it "should work like a convex hull", ->
      @bb.extend_pt(@p)
      @bb.extend_pt({x: -1, y: -3})
      expect(@bb.contains_pt({x: 0, y: 0})).toBe true

  describe "#recompute_from_points", ->

    beforeEach ->
      @bb = new AABB()
      @p = {x:1, y: 2}
      @p1 = {x:-2, y:-1}
      @p2 = {x:0, y: 0}

    it "should work for just one point", ->
      @bb.recompute_from_points([@p1])
      expect(@bb.contains_pt(@p1)).toBe true

    it "should contain the points it recomputed", ->
      @bb.recompute_from_points([@p1, @p2])
      expect(@bb.contains_pt(@p1)).toBe true
      expect(@bb.contains_pt(@p2)).toBe true

    it "should contain middle points", ->
      @bb.recompute_from_points([@p1, @p2])
      expect(@bb.contains_pt(@p)).toBe false


describe "Polygon", ->

  beforeEach ->
    @py0 = new Polygon()
    @py1 = new Polygon(@py0.points); @py1.push_point({x:0, y:0})
    @py2 = new Polygon(@py1.points); @py2.push_point({x:1, y:0})
    @py3 = new Polygon(@py2.points); @py3.push_point({x:1, y:1})
    @py4 = new Polygon(@py3.points); @py4.push_point({x:0, y:1})
    @py5 = new Polygon(@py4.points); @py5.push_point({x:-0.1, y:2})
    @pyZ1 = new Polygon([{x:0,y:0},{x:1,y:0},{x:0,y:1},{x:1,y:1}])
    @pyZ2 = new Polygon([{x:1,y:1},{x:0,y:1},{x:1,y:0},{x:0,y:0}])

  describe "#push_point", ->
    it "should add one more point", ->
      expect(@py0.points.length).toBe 0
      expect(@py1.points.length).toBe 1
      expect(@py2.points.length).toBe 2
      expect(@py3.points.length).toBe 3
      expect(@py4.points.length).toBe 4

  describe "#pop_point", ->
    it "should return the point", ->
      expect(@py1.pop_point()).toEqual {x:0, y:0}
      expect(@py2.pop_point()).toEqual {x:1, y:0}
      expect(@py3.pop_point()).toEqual {x:1, y:1}
      expect(@py4.pop_point()).toEqual {x:0, y:1}

    it "should have the right length", ->
      @py1.pop_point(); expect(@py1.points.length).toBe 0
      @py2.pop_point(); expect(@py2.points.length).toBe 1
      @py3.pop_point(); expect(@py3.points.length).toBe 2
      @py4.pop_point(); expect(@py4.points.length).toBe 3

  describe "#set_pt", ->
    it "should set the point", ->
      for py in [@py0, @py1, @py2, @py3, @py4]
        for i in [0..py.points.length]
          py.set_point(i, {x:2, y:2})
          expect(py.get_pt(i)).toEqual {x:2, y:2}

  describe "#can_push_point", ->
    it "should allow anything for <3 vertices", ->
      expect(@py0.can_push_point(x:0, y:0)).toBe true
      expect(@py1.can_push_point(x:1, y:0)).toBe true
      expect(@py2.can_push_point(x:1, y:1)).toBe true

    it "should allow non-intersecting pushes", ->
      expect(@py3.can_push_point(x:0, y:1)).toBe true
      expect(@py3.can_push_point(x:0.5, y:0.5)).toBe true
      expect(@py4.can_push_point(x:0.5, y:0.5)).toBe true
      expect(@py4.can_push_point(x:-1, y:0.5)).toBe true
      expect(@py4.can_push_point(x:0, y:2)).toBe true
      expect(@py4.can_push_point(x:1.5, y:1.5)).toBe true
      expect(@py5.can_push_point(x:-1, y:0.5)).toBe true
      for y in [-2..2]
        expect(@py3.can_push_point(x: 2, y:y)).toBe true
      for y in [-2..2]
        expect(@py4.can_push_point(x:-1, y:y)).toBe true

    it "should not allow intersecting pushes", ->
      for y in [-5..-1]
        expect(@py3.can_push_point(x: 0.5, y:y)).toBe false
        expect(@py4.can_push_point(x: 0.5, y:y)).toBe false
      for x in [2..5]
        expect(@py4.can_push_point(x:x, y:0.5)).toBe false

    it "should not allow closed polygons to push points", ->
      @py3.close(); @py4.close(); @py5.close()
      expect(@py3.can_push_point(x:0, y:1)).toBe false
      expect(@py4.can_push_point(x:0.5, y:0.5)).toBe false
      expect(@py5.can_push_point(x:-1, y:0.5)).toBe false

  describe "#can_close", ->
    it "should not allow closed polygons to close", ->
      for py in [@py0, @py1, @py2, @py3, @py4]
        py.close()
        expect(py.can_close()).toBe false

    it "should not allow lines or points to close", ->
      for py in [@py0, @py1]
        expect(py.can_close()).toBe false

    it "should allow normal shapes to close", ->
      for py in [@py3, @py4, @py5]
        expect(py.can_close()).toBe true

    it "should disallow invalid shapes to close", ->
      expect(@pyZ1.can_close()).toBe false
      expect(@pyZ2.can_close()).toBe false

  describe "#midpoint", ->
    it "should return the midpoint", ->
      expect(@py3.midpoint().x).toBeCloseTo(2/3, 1e-4)
      expect(@py3.midpoint().y).toBeCloseTo(1/3, 1e-4)
      expect(@py4.midpoint().x).toBeCloseTo(0.5, 1e-4)
      expect(@py4.midpoint().y).toBeCloseTo(0.5, 1e-4)

  describe "#centroid", ->
    it "should return the centroid", ->
      expect(@py3.centroid().x).toBeCloseTo(2/3, 1e-4)
      expect(@py3.centroid().y).toBeCloseTo(1/3, 1e-4)
      expect(@py4.centroid().x).toBeCloseTo(0.5, 1e-4)
      expect(@py4.centroid().y).toBeCloseTo(0.5, 1e-4)

  describe "#area", ->
    it "should return the area", ->
      expect(@py3.area()).toBeCloseTo(0.5, 1e-4)
      expect(@py4.area()).toBeCloseTo(1, 1e-4)

  describe "#intersects_segment", ->
    it "should return true when intersecting", ->
      for py in [@py2, @py3, @py4]
        expect(py.intersects_segment({x:0.5,y:-1},{x:0.5,y:2})).toBe true

    it "should return false when not intersecting", ->
      for py in [@py0, @py1, @py2, @py3, @py4]
        expect(py.intersects_segment({x:0.5,y:2},{x:0.5,y:3})).toBe false

  describe "#contains_pt", ->
    it "should not contain anything when a line or point", ->
      for py in [@py0, @py1, @py2]
        for p in @py4.points
          expect(py.contains_pt(p)).toBe false

    it "should return true when it contains a point", ->
      for py in [@py3, @py4]
        expect(py.contains_pt(x:0.2, y:0.1)).toBe true
        expect(py.contains_pt(x:0.9, y:0.1)).toBe true
      expect(@py4.contains_pt(x:0.1, y:0.9)).toBe true

    it "should return false when it doesn't contain a point", ->
      expect(@py3.contains_pt(x:0.1, y:0.9)).toBe false
      expect(@py4.contains_pt(x:-0.1, y:0.9)).toBe false
      for py in [@py0, @py1, @py2, @py3, @py4]
        expect(py.contains_pt(x:0.1, y:1.1)).toBe false
        expect(py.contains_pt(x:1.1, y:1.1)).toBe false

  describe "#self_intersects_at_index", ->
    it "should return false when valid", ->
      for py in [@py0, @py1, @py2, @py3, @py4]
        for p,i in py.points
          expect(py.self_intersects_at_index(i)).toBe false
        py.close()
        for p,i in py.points
          expect(py.self_intersects_at_index(i)).toBe false

    it "should return true when invalid", ->
      for py in [@py3, @py4]
        py.push_point(x: 0.5, y:-1)
        py.close()
        expect(py.self_intersects_at_index(py.points.length - 1)).toBe true
      for py in [@pyZ1, @pyZ2]
        py.close()
        expect(py.self_intersects_at_index(0)).toBe true
        expect(py.self_intersects_at_index(py.points.length - 1)).toBe true

  describe "#self_intersects", ->
    it "should return false when valid", ->
      for py in [@py0, @py1, @py2, @py3, @py4]
        expect(py.self_intersects()).toBe false

    it "should return true when invalid", ->
      for py in [@pyZ1, @pyZ2]
        py.close()
        expect(py.self_intersects()).toBe true

  describe "#partially_intersects_poly", ->
    it "should return true when edges intersect and open", ->
      for py1 in [@py3, @py4, @py5]
        for py2 in [@py3, @py4, @py5]
          expect(py1.partially_intersects_poly(py2)).toBe true

    it "should return true when edges intersect and closed", ->
      for py1 in [@py3, @py4, @py5]
        for py2 in [@py3, @py4, @py5]
          py1.close(); py2.close()
          expect(py1.partially_intersects_poly(py2)).toBe true

    it "should return true when edges intersect but points do not", ->
      py1 = new Polygon([{x:-1,y:0.2},{x:2,y:0.2},{x:2,y:0.8},{x:-1,y:0.8}])
      for py in [@py3, @py4, @py5, @pyZ1, @pyZ2]
        expect(py.partially_intersects_poly(py1)).toBe true
        expect(py1.partially_intersects_poly(py)).toBe true
        py.close()
        expect(py.partially_intersects_poly(py1)).toBe true
        expect(py1.partially_intersects_poly(py)).toBe true
      py1.close()
      for py in [@py3, @py4, @py5, @pyZ1, @pyZ2]
        expect(py.partially_intersects_poly(py1)).toBe true
        expect(py1.partially_intersects_poly(py)).toBe true

    it "should return false when not intersecting", ->
      for py in [@py3, @py4, @py5, @pyZ1, @pyZ2]
        py0 = new Polygon([{x:p.x+1.1, y:p.y+1.1} for p in py.points])
        py1 = new Polygon([{x:p.x-1.1, y:p.y-1.1} for p in py.points])
        expect(py.partially_intersects_poly(py0)).toBe false
        expect(py.partially_intersects_poly(py1)).toBe false
        expect(py0.partially_intersects_poly(py)).toBe false
        expect(py1.partially_intersects_poly(py)).toBe false

    it "should return false when containing", ->
      py0 = new Polygon([
        {x:0.8,y:0.1},{x:0.9,y:0.1},{x:0.9,y:0.2},{x:0.8,y:0.2}])
      for py in [@py3, @py4]
        expect(py.partially_intersects_poly(py0)).toBe false

  describe "#contains_poly", ->
    it "should return true when containing", ->
      py0 = new Polygon([
        {x:0.8,y:0.1},{x:0.9,y:0.1},{x:0.9,y:0.2},{x:0.8,y:0.2}])
      for py in [@py3, @py4]
        expect(py.contains_poly(py0)).toBe true

    it "should return false when intersecting", ->
      py1 = new Polygon([{x:-1,y:0.2},{x:2,y:0.2},{x:2,y:0.8},{x:-1,y:0.8}])
      for py in [@py3, @py4, @py5, @pyZ1, @pyZ2]
        expect(py.contains_poly(py1)).toBe false
        expect(py1.contains_poly(py)).toBe false
        py.close()
        expect(py.contains_poly(py1)).toBe false
        expect(py1.contains_poly(py)).toBe false
      py1.close()
      for py in [@py3, @py4, @py5, @pyZ1, @pyZ2]
        expect(py.contains_poly(py1)).toBe false
        expect(py1.contains_poly(py)).toBe false

    it "should return false when not containing", ->
      for py in [@py3, @py4]
        m = py.centroid()
        py0 = new Polygon([
          {x:(p.x+m.x*9)/10, y:(p.y+m.y*9)/10} for p in py.points])
        expect(py0.contains_poly(py)).toBe false

      for py in [@py3, @py4, @py5, @pyZ1, @pyZ2]
        py0 = new Polygon([{x:p.x+1.1, y:p.y+1.1} for p in py.points])
        py1 = new Polygon([{x:p.x-1.1, y:p.y-1.1} for p in py.points])
        expect(py.contains_poly(py0)).toBe false
        expect(py.contains_poly(py1)).toBe false
        expect(py0.contains_poly(py)).toBe false
        expect(py1.contains_poly(py)).toBe false

  describe "#intersects_poly", ->
    it "should intersect itself", ->
      for py in [@py3, @py4, @py5]
        expect(py.intersects_poly(py)).toBe true

    it "should return true when intersecting", ->
      for py1 in [@py3, @py4, @py5, @pyZ1, @pyZ2]
        for py2 in [@py3, @py4, @py5, @pyZ1, @pyZ2]
          expect(py1.intersects_poly(py2)).toBe true

    it "should return false when not intersecting", ->
      for py in [@py3, @py4, @py5, @pyZ1, @pyZ2]
        py0 = new Polygon([{x:p.x+1.1, y:p.y+1.1} for p in py.points])
        py1 = new Polygon([{x:p.x-1.1, y:p.y-1.1} for p in py.points])
        expect(py.intersects_poly(py0)).toBe false
        expect(py.intersects_poly(py1)).toBe false
        expect(py0.intersects_poly(py)).toBe false
        expect(py1.intersects_poly(py)).toBe false

describe "intersects_segment", ->
  it "should return true on intersection", ->
    expect(segments_intersect(
      {x:0,y:0},{x:1,y:0},{x:0.5,y:-1},{x:0.5,y:1})).toBe true

  it "should return false on non-intersection", ->
    expect(segments_intersect(
      {x:0,y:0},{x:0,y:1},{x:0.5,y:1},{x:0.5,y:2})).toBe false
    expect(segments_intersect(
      {x:0,y:0},{x:0,y:1},{x:0.5,y:-1},{x:0.5,y:1})).toBe false

describe "mod", ->
  it "should compute mod for positive numbers", ->
    for n in [3..7]
      for j in [0..100]
        expect(mod(j, n)).toEqual (j % n)

  it "should compute mod for negative numbers", ->
    for n in [3..7]
      for j in [-100..0]
        expect(mod(j, n)).toEqual ((j + 100*n) % n)
