# Displays an un-editable polygon on an image
# requires: common/util.coffee, kinetic.js
class PolyDisplay
  constructor: (args) ->
    @bbox = {width: args.width, height: args.height}
    @size = @bbox

    # create stage
    @stage = new Kinetic.Stage(
      container: args.container_id,
      width: @size.width, height: @size.height)
    @layer = new Kinetic.Layer()
    @stage.add(@layer)

    # create poly
    @set_photo(args.photo_url) if args.photo_url?
    if args.polygons?
      @set_polygons(args.polygons)
    else if args.vertices?
      @set_polygons([args.vertices])

  # change the polygons
  set_polygons: (polygons) ->
    @polygons = polygons

    if @k_polys?
      for k in @k_polys
        k.remove()

    @k_polys = []
    for vertices, i in @polygons
      # closure to isolate variables in each iteration
      do (i) =>
        # scale vertices up to width/height
        points = []
        for p, j in vertices
          if (j % 2) == 0
            points.push(p * @size.width)
          else
            points.push(p * @size.height)

        k_poly = new Kinetic.Polygon(
          points: points,
          stroke: POLYGON_COLORS[i % POLYGON_COLORS.length],
          strokeWidth: 3,
          lineJoin: 'round', opacity: 0.8,
        )
        k_poly.on('mouseover', do => =>
          k_poly.setFill('#fff')
          k_poly.setOpacity(0.4)
          @layer.draw()
        )
        k_poly.on('mouseout', do => =>
          k_poly.setFill('')
          k_poly.setOpacity(0.8)
          @layer.draw()
        )
        @layer.add(k_poly)
        @k_polys.push(k_poly)
    @layer.draw()

  # change the photo
  set_photo: (photo_url) ->
    if @k_photo?
      @k_photo.remove()

    @add_loading()
    @photo_obj = new Image()
    @photo_obj.onload = do => =>
      @remove_loading()
      @size = compute_dimensions(@photo_obj, @bbox)
      @stage.setWidth(@size.width)
      @stage.setHeight(@size.height)
      @k_photo = new Kinetic.Image(
        x: 0, y: 0, image: @photo_obj,
        width: @size.width, height: @size.height)
      @layer.add(@k_photo)
      @k_photo.moveToBottom()
      @set_polygons(@polygons) if @polygons?
      @layer.draw()
    @photo_obj.src = photo_url

  add_loading: ->
    window.loading_start?()
    if not @k_loading?
      @k_loading = new Kinetic.Text(
        x: 30, y: 30, text: "Loading...", align: "left",
        fontSize: 14, fontFamily: "Helvetica,Verdana,Ariel",
        textFill: "#000")
      @layer.add(@k_loading)
      @layer.draw()

  remove_loading: ->
    window.loading_finish?()
    if @k_loading?
      @k_loading.remove()
      @k_loading = null
      @layer.draw()
