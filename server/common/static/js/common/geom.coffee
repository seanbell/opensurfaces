# handy constants
INF = Number.POSITIVE_INFINITY
NINF = Number.NEGATIVE_INFINITY

# Axis-aligned bounding box (2D)
class AABB
  constructor: (min={x:INF,y:INF}, max={x:NINF,y:NINF}) ->
    @min = clone_pt(min)
    @max = clone_pt(max)

  # sets this to the empty AABB
  reset: ->
    @min={x:INF,y:INF}
    @max={x:NINF,y:NINF}

  # clone this AABB
  clone: ->
    new AABB(@min, @max)

  midpoint: ->
    x: 0.5 * (@min.x + @max.x)
    y: 0.5 * (@min.y + @max.y)

  # returns true if this contains point p
  contains_pt: (p) ->
    p.x >= @min.x and p.x <= @max.x and p.y >= @min.y and p.y <= @max.y

  # returns true if this intersects b
  intersects_bbox: (b) ->
    (@max.x >= b.min.x and @min.x <= b.max.x and
     @max.y >= b.min.y and @min.y <= b.max.y)

  # returns true if this entirely contains b
  contains_bbox: (b) ->
    (@max.x >= b.max.x and @min.x <= b.min.x and
     @max.y >= b.max.y and @min.y <= b.min.y)

  # expand the AABB to include a new point
  extend_pt: (p) ->
    @min = {x: Math.min(@min.x, p.x), y: Math.min(@min.y, p.y)}
    @max = {x: Math.max(@max.x, p.x), y: Math.max(@max.y, p.y)}

  # compute a new AABB from the given points
  recompute_from_points: (points) ->
    @reset()
    for p in points
      @extend_pt(p)

  normalize_pt: (p) ->
    x: (p.x - @min.x) / (@max.x - @min.x)
    y: (p.y - @min.y) / (@max.y - @min.y)


# Mathematical polygon (2D)
class Polygon
  constructor: (pts, @open = true) ->
    @aabb = new AABB()
    @points = []
    @push_points(pts) if pts?

  # add point (make sure to check can_push_point first)
  push_point: (p) -> if p?
    @points.push(clone_pt(p))
    @aabb.extend_pt(p)

  push_points: (pts) ->
    for p in pts
      @push_point(p)

  # remove last point
  pop_point: (p) ->
    if @points.length > 0
      ret = @points.pop()
      @aabb.recompute_from_points(@points)
      ret

  # move point index i to position p
  set_point: (i, p) -> if p?
    @points[i].x = p.x
    @points[i].y = p.y
    @aabb.recompute_from_points(@points)
    p

  # change close state (make sure to check can_close first)
  close: -> @open = false
  unclose: -> @open = true
  empty: -> @points.length == 0

  # point accessors
  get_pt: (i) -> clone_pt(@points[i])
  num_points: -> @points.length
  clone_points: -> (clone_pt(p) for p in @points)
  get_aabb: -> @aabb.clone()

  # returns true if p can be added
  can_push_point: (p) ->
    if not @open then return false
    if @points.length < 3 then return true
    return not @intersects_segment(
      @points[@points.length - 1], p, [@points.length - 2])

  # returns true if this poly can close without self-intersecting
  can_close: () ->
    if not @open or @points.length < 3 then return false
    if @points.length == 3 then return true
    return not @intersects_segment(@points[0],
      @points[@points.length - 1], [0, @points.length - 2])

  # return the average vertex position
  midpoint: ->
    if @points.length < 1 then return undefined
    x = y = 0
    for p in @points
      x += p.x
      y += p.y
    return {x: x/@points.length, y: y/@points.length}

  # returns the exact centroid
  centroid: ->
    if @points.length < 1 then return undefined
    A = Cx = Cy = 0
    for v0, i in @points
      v1 = @points[(i + 1) % @points.length]
      t = v0.x * v1.y - v1.x * v0.y
      A += t
      Cx += (v0.x + v1.x) * t
      Cy += (v0.y + v1.y) * t
    if Math.abs(A) < 0.001 then return @midpoint()
    return {x: Cx / (3 * A), y: Cy / (3 * A)}

  # return the midpoint of the axis-aligned bounding box
  aabb_midpoint: ->
    @aabb.midpoint()

  # returns exact area
  area: ->
    A = 0
    for v0, i in @points
      v1 = @points[(i + 1) % @points.length]
      A += v0.x * v1.y - v1.x * v0.y
    return Math.abs(A / 2)

  # returns a good position to place a label
  # requires: delaunay.js
  labelpos: ->
    # if the centroid is good enough, use it
    best_m = @centroid()
    if @contains_pt(best_m)
      best_d2 = @dist2_to_edge(best_m)
      if best_d2 > 2000 # good enough already
        return best_m
    else
      best_d2 = 0

    # delaunay triangulation (O(n^2) worst case)
    del_tri = delaunay_triangulate(@clone_points())

    # find the triangle midpoint that is inside the poly
    # and furthest from the edges
    for t in del_tri
      m = t.midpoint()
      if @contains_pt(m)
        d2 = @dist2_to_edge(m)
        if d2 > best_d2
          best_d2 = d2
          best_m = m

    return best_m

  # returns true iff this polygon is complex
  # (assumes non-self-intersecting)
  is_convex: ->
    s = true
    for v0, i in @points
      v1 = @points[(i + 1) % @points.length]
      v2 = @points[(i + 2) % @points.length]
      if i == 0
        s = ccw(v1, v0, v2)
      else if s != ccw(v1, v0, v2)
        return false
    return true

  # returns the closest squared distance from p to an edge
  dist2_to_edge: (p) ->
    n = @points.length
    if n < 2 then return 0
    min_d2 = Number.POSITIVE_INFINITY
    for v0, i in @points
      v1 = @points[(i + 1) % @points.length]
      min_d2 = Math.min(min_d2, seg_pt_dist2(v0.x, v0.y, v1.x, v1.y, p.x, p.y))
    return min_d2

  # returns true if this intersects the segment p1--p2
  intersects_segment: (p1, p2, excludes=[]) ->
    n = @points.length
    if n < 2 then return false
    max = if @open then (n-1) else n
    for i in [0...max] when i not in excludes
      v1 = @points[i]; v2 = @points[(i+1) % n]
      if segments_intersect(p1, p2, v1, v2) then return true
    return false

  # returns true if this polygon contains point p
  # adapted from http://www.ecse.rpi.edu/Homepages/wrf
  # /Research/Short_Notes/pnpoly.html
  contains_pt: (p) ->
    if @points.length < 3 or not @aabb.contains_pt(p) then return false
    n = @points.length; c = false; i = 0; j = n-1
    while i < n
      vi = @points[i]
      if vi.x == p.x and vi.y == p.y then return true
      vj = @points[j]
      if (((vi.y > p.y) != (vj.y > p.y)) and
          (p.x < (vj.x - vi.x) * (p.y - vi.y) / (vj.y - vi.y) + vi.x))
        c = not c
      j = i++
    return c

  # returns true if the polygon self-intersects at vertex i
  self_intersects_at_index: (i) ->
    if @points.length < 4 then return false
    m2 = mod(i - 2, @points.length)
    m1 = mod(i - 1, @points.length)
    p1 = mod(i + 1, @points.length)
    return @intersects_segment(@points[i], @points[p1], [m1, i, p1]) or
           @intersects_segment(@points[i], @points[m1], [m2, m1, i])

  # returns true if some segment of this polygon intersects another segment
  self_intersects: ->
    max = if @open then (@points.length-1) else @points.length
    for i in [0...max]
      if @self_intersects_at_index(i)
        return true
    return false

  # returns true if some edge of this polygon intersects poly
  # entire containment of one poly with the other returns false
  partially_intersects_poly: (poly) ->
    if not @aabb.intersects_bbox(poly.aabb) then return false
    n = @points.length
    if n < 2 then return false
    max = if @open then (n-1) else n
    for i in [0...max]
      v1 = @points[i]; v2 = @points[(i+1) % n]
      if poly.intersects_segment(v1, v2) then return true
    return false

  # returns true if this polygon entirely contains poly
  contains_poly: (poly) ->
    if not @aabb.contains_bbox(poly.aabb) then return false
    for p in poly.points
      if not @contains_pt(p) then return false
    return true

  # returns true if this polygon intersects poly
  intersects_poly: (poly) ->
    @contains_poly(poly) or @partially_intersects_poly(poly)


# Mathematical complex polygon (2D).
# Representation: list of vertices, triangles, and unorganized segments.
# Triangles and segments are indices into the list of vertices.
# Triangles are length-3 arrays, vertices are length-2 integer arrays.
class ComplexPolygon
  constructor: (vertices, triangles, segments) ->
    # clone the input arrays
    @vertices = vertices.splice(0)
    @triangles = triangles.splice(0)
    @segments = segments.splice(0)

    @aabb = new AABB()
    for p in @vertices
      @aabb.extend_pt(p)

  # computes the centroid of this polygon
  centroid: ->
    sum_x = 0
    sum_y = 0
    sum_a = 0
    for t in @triangles_points()
      m = mean_pt(t)
      a = tri_area(t[0], t[1], t[2])
      sum_x += m.x * a
      sum_y += m.y * a
      sum_a += a
    x: sum_x / sum_a
    y: sum_y / sum_a

  get_aabb: -> @aabb.clone()

  aabb_midpoint: ->
    @aabb.midpoint()

  contains_pt: (p) ->
    if not @aabb.contains_pt(p) then return false
    for t in @triangles_points()
      if pt_in_tri(t[0], t[1], t[2], p)
        return true
    return false

  # returns a good position to place a label
  labelpos: ->
    centroid = @centroid()
    if @contains_pt(centroid)
      best_m = centroid
      best_d2 = @dist2_to_edge(centroid)
    else
      best_d2 = NINF
    for t in @triangles_points()
      m = mean_pt(t)
      d2 = @dist2_to_edge(m)
      if d2 > best_d2
        best_d2 = d2
        best_m = m
    return best_m

  # returns the smallest squared distance from p to an edge
  dist2_to_edge: (p) ->
    min_d2 = Number.POSITIVE_INFINITY
    for s in @segments
      v0 = @vertices[s[0]]
      v1 = @vertices[s[1]]
      min_d2 = Math.min(min_d2, seg_pt_dist2(v0.x, v0.y, v1.x, v1.y, p.x, p.y))
    return min_d2

  # returns a list of line segments as nested point arrays
  segments_points: ->
    ([@vertices[s[0]], @vertices[s[1]]] for s in @segments)

  # returns a list of triangles as nested point arrays
  triangles_points: ->
    ([@vertices[t[0]], @vertices[t[1]], @vertices[t[2]]] for t in @triangles)


# Represents a pinhole camera model but without a transform (located at the
# origin)
class Perspective
  constructor: (args) ->
    if args.focal?
      @f = args.focal
    else if args.width? and args.fov?
      @f = args.width / (2 * Math.tan(args.fov / 2))
    else
      console.log args
      throw {name: "error: bad arguments", args: args}

  project: (p) ->
    {x: @f * p.x / p.z, y: @f * p.y / p.z}

  unproject: (p, z=p.z) ->
    {x: p.x * p.z / @f, y: p.y * p.z / @f, z: z}


# returns true if AB intersects CD (2D)
segments_intersect = (A, B, C, D) ->
  ccw(A, C, D) isnt ccw(B, C, D) and ccw(A, B, C) isnt ccw(A, B, D)
ccw = (A, B, C) -> (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x)

# squared point-segment distance
seg_pt_dist2 = (x1, y1, x2, y2, px, py) ->
  pd2 = (x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2)

  if (pd2 == 0)
    # Points are coincident.
    x = x1
    y = y2
  else
    # parameter of closest point on the line
    u = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / pd2
    if (u < 0) # off the end
      x = x1
      y = y1
    else if (u > 1.0) # off the end
      x = x2
      y = y2
    else # interpolate
      x = x1 + u * (x2 - x1)
      y = y1 + u * (y2 - y1)

  return (x - px) * (x - px) + (y - py) * (y - py)

# converts an object having an x and y attribute (possibly z) into a point
clone_pt = (o) ->
  if o?
    if o.z?
      {x: o.x, y: o.y, z: o.z}
    else
      {x: o.x, y: o.y}
  else
    null


# distance between p and q
dist_pt = (p, q) ->
  dx = p.x - q.x
  dy = p.y - q.y
  Math.sqrt(dx * dx + dy * dy)


# subtract two points
sub_pt = (p, q) -> {x: p.x - q.x, y: p.y - q.y}


# computes the mean position of a list of points
mean_pt = (points) ->
  x = 0
  y = 0
  for p in points
    x += p.x
    y += p.y
  {x: x/points.length, y: y/points.length}


# computes the area of the triangle a,b,c
tri_area = (a, b, c) ->
  0.5 * Math.abs(a.x * (b.y - c.y) + b.x * (c.y - a.y) + c.x * (a.y - b.y))


# return whether v is in the triangle a,b,c
# (from http://mathworld.wolfram.com/TriangleInterior.html)
pt_in_tri = (a, b, c, v) ->
  det = (u, v) -> u.x * v.y - u.y * v.x
  v0 = a
  v1 = sub_pt(b, a)
  v2 = sub_pt(c, a)
  det_v1v2 = det(v1, v2)
  a = (det(v, v2) - det(v0, v2)) / det_v1v2
  if a < 0 or a > 1 then return false
  b = -(det(v, v1) - det(v0, v1)) / det_v1v2
  return b >= 0 and a + b <= 1

# computes mod, wrapping around negative numbers properly
mod = (x,n) -> ((x % n) + n) % n
