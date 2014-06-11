matrix4_from_vector3 = (fx, fy, fz) ->
  return new THREE.Matrix4(
    fx.x, fy.x, fz.x, 0
    fx.y, fy.y, fz.y, 0
    fx.z, fy.z, fz.z, 0
    0, 0, 0, 1
  )

matrix4_from_xz = (x, z) ->
  y = new THREE.Vector3()
  y.cross(z, x).normalize()
  z.cross(x, y).normalize()
  x.normalize()
  matrix4_from_vector3(x, y, z)

matrix4_from_yz = (y, z) ->
  x = new THREE.Vector3()
  x.cross(y, z).normalize()
  y.cross(z, x).normalize()
  z.normalize()
  matrix4_from_vector3(x, y, z)

perterb_normal = (n, dx, dy) ->
  n.x += dx
  n.y += dy
  n_len2 = n.x * n.x + n.y * n.y
  if n_len2 > 1
    s = 1 / Math.sqrt(n_len2)
    n.x *= s
    n.y *= s
    n.z = 0
  else
    n.z = Math.sqrt(1 - n_len2)
  n

# Wrapper for Kinetic.Stage
class StageUI
  constructor: (args) ->
    @bbox = {width: args.width, height: args.height}
    @dims = {width: args.width, height: args.height}
    @stage = new Kinetic.Stage(
      container: args.container_id,
      width: @bbox.width,
      height: @bbox.height)
    @layer = new Kinetic.Layer()
    @stage.add(@layer)

    # zoom information
    @origin = {x: 0, y: 0}
    @zoom_exp = 0
    @zoom_exp_max = 3

  zoom_reset: ->
    @zoom_exp = 0
    @origin = {x: 0, y: 0}
    @stage.setPosition(0, 0)
    @stage.setOffset(@origin.x, @origin.y)
    @stage.setScale(1.0)
    @stage.draw()

  # zoom in/out by delta (in log_2 units)
  zoom_delta: (delta, p=@stage.getMousePosition()) ->
    if delta?
      @zoom_set(@zoom_exp + delta * 0.001, p)

  zoom_set: (new_zoom_exp, p=@stage.getMousePosition()) ->
    if @k_loading? or not new_zoom_exp? or not p? then return
    old_scale = Math.pow(2, @zoom_exp)
    @zoom_exp = Math.min(@zoom_exp_max, new_zoom_exp)
    if @zoom_exp <= 0
      @zoom_reset()
    else
      new_scale = Math.pow(2, @zoom_exp)
      f = (1.0 / old_scale - 1.0 / new_scale)
      @origin.x += f * p.x
      @origin.y += f * p.y
      @stage.setOffset(@origin.x, @origin.y)
      @stage.setScale(new_scale)
      @stage.draw()

  draw: -> @layer.draw()

  mouse_pos: (e) -> @stage.getMousePos(e)

  add: (o, opacity=1.0, duration=0.4) ->
    @layer.add(o)
    if duration > 0
      o.setOpacity(opacity)
      o.add_trans = o.transitionTo(opacity:opacity, duration:duration)

  remove: (o, duration=0.4) ->
    o.add_trans?.stop()
    if duration > 0
      o.transitionTo(opacity: 0, duration: duration,
        callback: do (o) -> -> o.remove())
    else
      o.remove()

  to_kinetic_coords: (points) ->
    w2 = @dims.width / 2
    h2 = @dims.height / 2
    ({x: p.x + w2, y: h2 - p.y} for p in points)

  # highlight the user's attention to a specific polygon by flashing
  # its area
  flash_triangles: (triangles) ->
    flashes = []
    for tri in triangles
      flashes.push(new Kinetic.Polygon(
        points: @to_kinetic_coords(tri),
        opacity: 0.4, fill: '#fff'))

    show_flash = =>
      for f in flashes
        @layer.add(f, 0.5, 0)
      @layer.draw()

    hide_flash = =>
      for f in flashes
        f.remove(f, 0)
      @layer.draw()

    setTimeout(( ->
      show_flash()
      setTimeout(( ->
        hide_flash()
        setTimeout(( ->
          show_flash()
          setTimeout(( ->
            hide_flash()
          ), 250)
        ), 250)
      ), 250)
    ), 250)

  add_loading: -> if not @k_loading?
    window.loading_start() if window.loading_start?
    @k_loading = new Kinetic.Text(
      x: 30, y: 30, text: 'Loading...', align: 'left',
      fontSize: 12, fontFamily: 'Helvetica,Verdana,Ariel',
      textFill: '#000')
    @add(@k_loading)
    @draw()

  remove_loading: -> if @k_loading?
    window.loading_finish() if window.loading_finish?
    @remove(@k_loading)
    @k_loading = null
    @draw()

  set_photo: (photo_url, on_load) ->
    if @photo_url == photo_url
      @dims = compute_dimensions(@photo_obj, @bbox)
      on_load(@dims) if on_load?
    else
      @photo_url = photo_url
      @add_loading()
      @photo_obj = new Image()
      @photo_obj.onload = do() => =>
        @remove_loading()
        if @photo?
          @photo.remove()
        @dims = compute_dimensions(@photo_obj, @bbox)
        @photo = new Kinetic.Image(
          x: 0, y: 0, image: @photo_obj,
          width: @dims.width, height: @dims.height)
        @layer.add(@photo)
        @photo.moveToBottom()
        on_load(@dims) if on_load?
      @photo_obj.src = photo_url

# UI for a normal
class NormalUI
  constructor: (@stage, dims, uvnb_elements) ->
    @uvnb_checkpoint = null
    @proj = new THREE.Matrix4()
    @uvnb = new THREE.Matrix4()
    for v, i in uvnb_elements
      @uvnb.elements[i] = v
    # placeholders
    @focal_pixels = 1
    @dims = {width: 1, height: 1}

  set_pos: (pos, focal_pixels) ->
    @pos = pos
    @focal_pixels = focal_pixels
    @update()

  update_proj: ->
    @depth = @focal_pixels / 20
    b_z = -@depth
    #@uvnb.elements[12] = -@pos.x * b_z / @focal_pixels
    #@uvnb.elements[13] = -@pos.y * b_z / @focal_pixels
    #@uvnb.elements[14] = b_z
    #@uvnb.elements[15] = 1
    K = new THREE.Matrix4(
      @focal_pixels, 0, 0, 0,
      0, @focal_pixels, 0, 0,
      0, 0, 0, 1,
      0, 0, -1, 0,
    )
    @proj.multiply(K, @uvnb)
    if window.rectify_ready
      rec_frame.setProjection(@uvnb, @focal_pixels)

  drag: (delta, mouserotate, local_frame) =>
    if delta.x == 0 and delta.y == 0
      return
    # drag the tip of the needle in cartesian coordinates
    uvn = new THREE.Matrix4()
    uvn.extractRotation(@uvnb)
    e = @uvnb.elements
    if mouserotate
      if local_frame
        rotateZ = new THREE.Matrix4().rotateZ(delta.y * 0.005)
      else
        rotateZ = new THREE.Matrix4().rotateZ(-delta.y * 0.005)
      uvn_new = new THREE.Matrix4().multiply(uvn, rotateZ)
    else
      if local_frame
        # rotate in the local frame (i.e. the coordinate frame on
        # the plane that we are rectifying)
        rotU = new THREE.Matrix4().rotateX(-delta.y * 0.005)
        rotV = new THREE.Matrix4().rotateY(-delta.x * 0.005)
        rotUV = new THREE.Matrix4().multiply(rotU, rotV)
        uvn_new = new THREE.Matrix4().multiply(uvn, rotUV)
      else
        # first put n into a frame with its z axis facing the camera

        f = new THREE.Matrix4().lookAt(
          new THREE.Vector3(0, 0, 0),
          new THREE.Vector3(e[12], e[13], e[14]),
          new THREE.Vector3(0, 1, 0)
        )

        # project n into frame
        n = new THREE.Vector4(e[8], e[9], e[10], 0)
        (new THREE.Matrix4().getInverse(f)).multiplyVector4(n)
        # perterb n
        perterb_normal(n, delta.x * 0.004, -delta.y * 0.004)
        # unproject from frame
        f.multiplyVector4(n)
        # re-orthogonalize
        v = new THREE.Vector3(e[4], e[5], e[6])
        uvn_new = matrix4_from_yz(v, n)

    ne = uvn_new.elements
    len_b = Math.sqrt(e[12] * e[12] + e[13] * e[13] + e[14] * e[14])
    if ne[8] * e[12] + ne[9] * e[13] + ne[10] * e[14] < 0
      do_rotation = true
      if local_frame and @uvnb_checkpoint != null
        ce = @uvnb_checkpoint.elements
        if ce[8] * ne[8] + ce[9] * ne[9] + ce[10] * ne[10] < 0.96
          do_rotation = false
      else
        @uvnb_checkpoint = @uvnb.clone()
      if do_rotation
        @uvnb.extractRotation(uvn_new)
    @update()
    @stage.draw()

  project: (v) ->
    q = v.clone()
    @proj.multiplyVector3(q)
    {x: q.x, y: q.y}

  update: ->
    @update_proj()

    ellipse_points = []
    for i in [0...64]
      cos = Math.cos(2 * Math.PI * i / 64)
      sin = Math.sin(2 * Math.PI * i / 64)
      ellipse_points.push(
        @project(new THREE.Vector3(cos, sin, 0))
      )
    ellipse_points = @stage.to_kinetic_coords(ellipse_points)

    if not @ellipse?
      @ellipse = new Kinetic.Polygon(
        fill: '#3c77cc',
        stroke: 'black',
        strokeWidth: 2,
        points: ellipse_points
      )
      @stage.add(@ellipse, 0.5)
    else
      @ellipse.setPoints(ellipse_points)
    @ellipse.moveToTop()

    u_line_points = @stage.to_kinetic_coords(
      [@project(new THREE.Vector3(0, 0, 0)),
       @project(new THREE.Vector3(1, 0, 0))])
    if not @u_line?
      @u_line = new Kinetic.Line(
        points: u_line_points,
        stroke: '#000',
        strokeWidth: 2,
        lineCap: 'round',
        lineJoin: 'round',
      )
      @stage.add(@u_line)
    else
      @u_line.setPoints(u_line_points)
    @u_line.moveToTop()

    v_line_points = @stage.to_kinetic_coords(
      [@project(new THREE.Vector3(0, 0, 0)),
       @project(new THREE.Vector3(0, 1, 0))])
    if not @v_line?
      @v_line = new Kinetic.Line(
        points: v_line_points,
        stroke: '#000',
        strokeWidth: 2,
        lineCap: 'round',
        lineJoin: 'round',
      )
      @stage.add(@v_line)
    else
      @v_line.setPoints(v_line_points)
    @v_line.moveToTop()

    n_line_points = @stage.to_kinetic_coords(
      [@project(new THREE.Vector3(0, 0, 0)),
       @project(new THREE.Vector3(0, 0, 1))])
    if not @line?
      @line = new Kinetic.Line(
        points: n_line_points,
        stroke: '#f00',
        strokeWidth: 3,
        lineCap: 'round',
        lineJoin: 'round',
      )
      @stage.add(@line)
    else
      @line.setPoints(n_line_points)
    @line.moveToTop()


# UI for a polygon
class PolygonUI
  constructor: (@stage) ->
    @poly = null

  set_poly: (poly, dims) ->
    @poly = poly
    @dims = dims
    @update()

  update: ->
    if @k_segs?
      for k in @k_segs
        @stage.remove(k, 0)

    @k_segs = []
    for points in @poly.segments_points()
      k_seg = new Kinetic.Polygon(
        points: @stage.to_kinetic_coords(points),
        stroke: '#f00', opacity: 0.5, strokeWidth: 2)
      @stage.add(k_seg, 0.5, 0)
      @k_segs.push(k_seg)

# Main logic controller
class NormalController
  constructor: (args) ->
    @ready = false
    @idx = -1
    @stage = new StageUI(args)
    @dims = {width:args.width, height: args.height}
    @normal_ui = new NormalUI(@stage, @dims, args.uvnb)
    @poly_ui = new PolygonUI(@stage)
    @downpos = null
    @mouserotate = false
    @fine = false
    @update(args.shape, args.uvnb)

  update: (cur, uvnb) ->
    photo_url = select_image_url(cur.photo.image, @dims.width)
    @stage.set_photo(photo_url, (dims) =>
      @dims = dims

      # convert to format for complex polygon object
      verts = []
      for i in [0...cur.vertices.length/2]
        verts.push(
          x: (cur.vertices[i*2] - 0.5) * dims.width,
          y: (0.5 - cur.vertices[i*2+1]) * dims.height,
        )
      tris = []
      for i in [0...cur.triangles.length/3]
        tris.push([
          cur.triangles[i*3],
          cur.triangles[i*3+1],
          cur.triangles[i*3+2],
        ])
      segs = []
      for i in [0...cur.segments.length/2]
        segs.push([
          cur.segments[i*2],
          cur.segments[i*2+1],
        ])

      @poly = new ComplexPolygon(verts, tris, segs)
      pos = @poly.labelpos()

      focal_pixels = 0.5 * Math.max(dims.width, dims.height) /
        Math.tan(0.5 * cur.photo.fov * Math.PI / 180.0)

      @poly_ui.set_poly(@poly, dims)
      @normal_ui.set_pos(pos, focal_pixels)
      @stage.draw()
    )
