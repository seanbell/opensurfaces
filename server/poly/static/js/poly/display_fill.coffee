# Displays an un-editable polygon in an image, so that the polygon fills the
# area.  Handles both simple and complex polygons.
# requires: common/util.coffee, kinetic.js
class PolyDisplayFill
  constructor: (args) ->
    @bbox = {width: args.width, height: args.height}
    @padding = if args.padding? then args.padding else 0.1

    # create stage
    @stage = new Kinetic.Stage(
      container: args.container_id,
      width: @bbox.width, height: @bbox.height)
    @layer = new Kinetic.Layer()
    @stage.add(@layer)

    # initial display
    if args.photo_url? and args.vertices?
      @set_display(args.photo_url, args.vertices, args.triangles, args.segments)

  # change the displayed polygon.  for simple polygons, do not specify
  # triangles or segments.
  set_display: (photo_url, vertices_unit, triangles, segments) ->
    @vertices_unit = vertices_unit
    @triangles = triangles
    @segments = segments
    if @triangles and @segments
      @complex = true
    else
      @complex = false

    # remove old photo
    if @k_photo?
      @k_photo.remove()

    # load photo
    @add_loading()
    @photo_obj = new Image()
    @photo_obj.onload = do => =>
      # convert vertices to pixel coordinates
      @vertices = []
      min_x = 1
      min_y = 1
      max_x = 0
      max_y = 0
      for p, i in @vertices_unit
        if (i % 2) == 0
          @vertices.push(p * @photo_obj.width)
          min_x = Math.min(min_x, p)
          max_x = Math.max(max_x, p)
        else
          @vertices.push(p * @photo_obj.height)
          min_y = Math.min(min_y, p)
          max_y = Math.max(max_y, p)

      @margin =
        width: Math.max(min_x, 1 - max_x)
        height: Math.max(min_y, 1 - max_y)

      # find bounds of vertices
      max = {x: 0, y: 0}
      min = {x: @photo_obj.width, y: @photo_obj.height}
      for p, i in @vertices
        if (i % 2) == 0
          max.x = Math.max(max.x, p)
          min.x = Math.min(min.x, p)
        else
          max.y = Math.max(max.y, p)
          min.y = Math.min(min.y, p)

      @vertices_size =
        width: (max.x - min.x),
        height: (max.y - min.y)

      # fill bbox with vertex bounds
      @poly_size = compute_dimensions(@vertices_size, {
        width: @bbox.width * (1 - 2 * Math.min(@padding, @margin.width)),
        height: @bbox.height * (1 - 2 * Math.min(@padding, @margin.height))
      })

      # center polygon
      @poly_offset =
        x: 0.5 * (@bbox.width - @poly_size.width)
        y: 0.5 * (@bbox.height - @poly_size.height)

      # scale up to width/height
      for p, i in @vertices
        if (i % 2) == 0
          @vertices[i] = (p - min.x) * @poly_size.scale + @poly_offset.x
        else
          @vertices[i] = (p - min.y) * @poly_size.scale + @poly_offset.y

      # create polygon object
      if @complex
        # remove old triangles and segments
        if @k_tris?
          for k in @k_tris
            k.remove()
        if @k_segs?
          for k in @k_segs
            k.remove()

        # add new triangles and segments
        @k_tris = []
        for t in [0...@triangles.length/3]
          k_tri = new Kinetic.Polygon(
            points: [
              @vertices[@triangles[t*3  ]*2  ],
              @vertices[@triangles[t*3  ]*2+1],
              @vertices[@triangles[t*3+1]*2  ],
              @vertices[@triangles[t*3+1]*2+1],
              @vertices[@triangles[t*3+2]*2  ],
              @vertices[@triangles[t*3+2]*2+1]
            ],
            opacity: 0.8,
          )
          k_tri.on('mouseover', do => =>
            for k in @k_tris
              k.setFill('#fff')
              k.setOpacity(0.3)
            for k in @k_segs
              k.setStroke('#700')
            @layer.draw()
          )
          k_tri.on('mouseout', do => =>
            for k in @k_tris
              k.setFill('')
              k.setOpacity(0.8)
            for k in @k_segs
              k.setStroke('#f00')
            @layer.draw()
          )
          @layer.add(k_tri)
          @k_tris.push(k_tri)

        @k_segs = []
        for t in [0...@segments.length/2]
          k_seg = new Kinetic.Line(
            points: [
              @vertices[@segments[t*2  ]*2  ],
              @vertices[@segments[t*2  ]*2+1],
              @vertices[@segments[t*2+1]*2  ],
              @vertices[@segments[t*2+1]*2+1]
            ],
            stroke: '#f00', strokeWidth: 3, opacity: 0.8,
          )
          @layer.add(k_seg)
          @k_segs.push(k_seg)
      else
        if not @k_fill?
          @k_fill = new Kinetic.Polygon(
            points: @vertices,
            stroke: '#f00', strokeWidth: 3,
            lineJoin: 'round', opacity: 0.8,
          )
          @k_fill.on('mouseover', do => =>
            @k_fill.setFill('#fff')
            @k_fill.setOpacity(0.3)
            @layer.draw()
          )
          @k_fill.on('mouseout', do => =>
            @k_fill.setFill('')
            @k_fill.setOpacity(0.8)
            @layer.draw()
          )
          @layer.add(@k_fill)
        else
          @k_fill.setPoints(@vertices)

      # add photo
      @photo_size =
        width: @photo_obj.width * @poly_size.scale
        height: @photo_obj.height * @poly_size.scale
      @photo_offset =
        x: @poly_offset.x - @poly_size.scale * min.x
        y: @poly_offset.y - @poly_size.scale * min.y
      @k_photo = new Kinetic.Image(
        x: @photo_offset.x, y: @photo_offset.y, image: @photo_obj,
        width: @photo_size.width, height: @photo_size.height)
      @layer.add(@k_photo)
      @k_photo.moveToBottom()

      # done
      @remove_loading()
      @layer.draw()

    @photo_obj.src = photo_url

  highlight_poly: ->
    if @complex
      if @k_segs?
        for k in @k_segs
          k.setStrokeWidth(6)
        @layer.draw()
    else
      if @k_fill?
        @k_fill.setStrokeWidth(6)
        @layer.draw()

  unhighlight_poly: ->
    if @complex
      if @k_segs?
        for k in @k_segs
          k.setStrokeWidth(3)
        @layer.draw()
    else
      if @k_fill?
        @k_fill.setStrokeWidth(3)
        @layer.draw()

  add_loading: ->
    window.loading_start() if window.loading_start?
    if not @k_loading?
      @k_loading = new Kinetic.Text(
        x: 30, y: 30, text: "Loading...", align: "left",
        fontSize: 14, fontFamily: "Helvetica,Verdana,Ariel", textFill: "#000")
      @layer.add(@k_loading)
      @layer.draw()

  remove_loading: ->
    window.loading_finish() if window.loading_finish?
    if @k_loading?
      @k_loading.remove()
      @k_loading = null
      @layer.draw()

  is_loading: ->
    @k_loading?
