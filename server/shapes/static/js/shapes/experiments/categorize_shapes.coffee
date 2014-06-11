# Wrapper for Kinetic.Stage
class StageUI
  constructor: (args) ->
    @dims = {width: args.width, height: args.height}
    @stage = new Kinetic.Stage(
      container: args.container_id,
      width: @dims.width,
      height: @dims.height,
      draggable: true
    )
    @layer = new Kinetic.Layer()
    @stage.add(@layer)

    # zoom information
    @origin = {x: 0, y: 0}
    @zoom_exp = 0
    @zoom_exp_max = 3

  draw: -> @layer.draw()

  mouse_pos: ->
    p = @stage.getMousePosition()
    if not p?
      p
    else
      scale = Math.pow(2, -@zoom_exp)
      x: Math.min(Math.max(0, p.x * scale + @origin.x), @size.width)
      y: Math.min(Math.max(0, p.y * scale + @origin.y), @size.height)

  add: (o, opacity=1.0, duration=0.4) ->
    @layer.add(o)
    if duration > 0
      o.setOpacity(0)
      o.add_trans = new Kinetic.Tween(
        node: o
        duration: duration
        opacity: opacity
      )
      o.add_trans.play()
    else
      o.setOpacity(opacity)

  remove: (o, duration=0.4) ->
    o.add_trans?.destroy()
    if duration > 0
      tween = new Kinetic.Tween(
        node: o
        opacity: 0
        duration: duration
        onFinish: do (o) -> ->
          o.remove()
          tween.destroy()
      )
      tween.play()
    else
      o.remove()

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
      @origin.x = p.x - @stage.getWidth() / (2 * new_scale)
      @origin.y = p.y - @stage.getHeight() / (2 * new_scale)
      @stage.setOffset(@origin.x, @origin.y)
      @stage.setScale(new_scale)
      @stage.draw()

  bbox_anim: (bbox) ->
    setTimeout(( =>
      rect = new Kinetic.Rect(
        x: 0, y: 0, width: @stage.getWidth(), height: @stage.getHeight(),
        stroke: '#f00', strokeWidth: 2, opacity: 0
      )
      @layer.add(rect)
      tween = new Kinetic.Tween(
        node: rect,
        x: bbox.min.x,
        y: bbox.min.y,
        width: bbox.max.x - bbox.min.x,
        height: bbox.max.y - bbox.min.y,
        opacity: 1.0,
        duration: 0.4,
        easing: Kinetic.Easings.EaseOut,
        onFinish: ->
          rect.remove()
          tween.destroy()
      )
      tween.play()
    ), 100)

  # highlight the user's attention to a specific polygon by flashing
  # its area
  flash_triangles: (triangles) ->
    flashes = []
    for tri in triangles
      flashes.push(new Kinetic.Polygon(points: tri, opacity: 0.5, fill: '#fff'))

    show_flash = =>
      for f in flashes
        @layer.add(f)
      @layer.draw()

    hide_flash = =>
      for f in flashes
        f.remove(f)
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
    @k_loading = new Kinetic.Text(
      x: 30, y: 30, text: 'Loading...', align: 'left',
      fontSize: 48, fontFamily: 'Helvetica,Verdana,Ariel',
      textFill: '#f00', textStroke: '#000', textStrokeWidth: 1)
    @add(@k_loading)
    @draw()

  remove_loading: -> if @k_loading?
    @remove(@k_loading, 0)
    @k_loading = null
    @draw()

  set_photo: (photo_url, on_load) ->
    if @photo_url == photo_url
      dims = compute_dimensions(@photo_obj, @dims)
      on_load(dims) if on_load?
    else
      @photo_url = photo_url
      @add_loading()
      @photo_obj = new Image()
      @photo_obj.onload = do() => =>
        @remove_loading()
        if @photo?
          @photo.remove()
        dims = compute_dimensions(@photo_obj, @dims)
        @photo = new Kinetic.Image(
          x: 0, y: 0, image: @photo_obj,
          width: dims.width, height: dims.height)
        @layer.add(@photo)
        @photo.moveToBottom()
        on_load(dims) if on_load?
      @photo_obj.src = photo_url

# UI for a polygon
class PolygonUI
  constructor: (@stage) ->
    @poly = null

  set_poly: (poly) ->
    @poly = poly
    @update()

  update: ->
    if @k_segs?
      for k in @k_segs
        @stage.remove(k, 0)

    @k_segs = []
    for points in @poly.segments_points()
      k_seg = new Kinetic.Polygon(
        points: points, stroke: '#f00', opacity: 0.5,
        strokeWidth: 2, lineJoin: 'round', lineCap: 'round')
      @stage.add(k_seg, 0.5, 0)
      @k_segs.push(k_seg)

# Main logic controller
class Controller
  constructor: (args) ->
    @ready = false
    @idx = -1
    @stage = new StageUI(args)
    @poly_ui = new PolygonUI(@stage)

    btn_submit = (category) =>
      if @ready
        $('.cat').removeClass('active')
        shape = window.mt_contents[@idx]
        shape.time_ms = shape.timer.time_ms()
        shape.time_active_ms = shape.timer.time_active_ms()
        shape.category = category
        console.log shape
        @next_shape()
      else
        window.show_modal_error("The page has not finished loading yet")

    $('.cat').on('mousedown', ->
      $('.cat').removeClass('active')
      $(this).addClass('active')
    )

    $('.cat').on('mouseup', -> btn_submit($(@).find('a').text()))

    $('#btn-back').on('click', @prev_shape)

    $('canvas').on('click', =>
      if @poly_ui? and @poly_ui.poly?
        @stage.flash_triangles(@poly_ui.poly.triangles_points())
    )

    $('#btn-zoom-in').on('click', =>
      if @poly_ui? and @poly_ui.poly?
        @stage.zoom_delta(800, @poly_ui.poly.centroid())
    )
    $('#btn-zoom-out').on('click', =>
      @stage.zoom_reset()
    )

    # disable text selection
    $(document).on('selectstart', -> false)

    @next_shape()

  prev_shape: =>
    if @idx > 0
      $('.btn-zoom').attr('disabled', 'disabled')
      @idx -= 1
      @update()

  next_shape: ->
    if @idx < window.mt_contents.length - 1
      $('.btn-zoom').attr('disabled', 'disabled')
      @idx += 1
      @update()
    else
      btn_submit_ok()

  update: ->
    @ready = false
    $('#image-count').text(@idx + 1)
    if @idx > 0
      $('#btn-back').removeAttr('disabled')
    else
      $('#btn-back').attr('disabled', 'disabled')
    cur = window.mt_contents[@idx]
    @stage.set_photo(cur.photo.url, (dims) =>
      $('.btn-zoom').removeAttr('disabled')

      # convert to format for complex polygon object
      verts = []
      for i in [0...cur.vertices.length/2]
        verts.push(
          x: cur.vertices[i*2] * dims.width,
          y: cur.vertices[i*2+1] * dims.height,
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

      poly = new ComplexPolygon(verts, tris, segs)
      pos = poly.labelpos()

      @poly_ui.set_poly(poly)
      @stage.zoom_reset()
      @stage.draw()

      @stage.flash_triangles(poly.triangles_points())
      @stage.bbox_anim(poly.get_aabb())
      window.mt_contents[@idx].timer = new ActiveTimer()
      window.mt_contents[@idx].timer.start()

      @ready = true
    )

btn_submit_ok = ->
  results = {}
  time_ms = {}
  time_active_ms = {}
  for c in window.mt_contents
    results[c.id] = c.category
    time_ms[c.id] = c.time_ms
    time_active_ms[c.id] = c.time_active_ms

  window.mt_submit( ->
    version: "1.0"
    results: JSON.stringify(results)
    time_ms: JSON.stringify(time_ms)
    time_active_ms: JSON.stringify(time_active_ms)
  )
