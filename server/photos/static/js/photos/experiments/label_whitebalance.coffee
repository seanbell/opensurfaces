$( ->
  args =
    container_id: 'mt-container',
    width: $('#mt-container').width(),
    height: $(window).height() - $('#mt-top-padding').height() - 16
    photo_url: window.mt_photos[0].url
  window.photo_whitebalance = new PhotoWhitebalance(args)
)

btn_submit_ok = ->
  window.mt_submit( ->

    results = {}
    time_ms = {}
    time_active_ms = {}
    for c in window.mt_photos
      results[c.id] = c.points  # x1,y1,x2,y2,... string
      time_ms[c.id] = c.time_ms
      time_active_ms[c.id] = c.time_active_ms

    version: '1.0'
    results: JSON.stringify(results)
    time_ms: JSON.stringify(time_ms)
    time_active_ms: JSON.stringify(time_active_ms)
  )

class PhotoWhitebalance
  constructor: (args) ->
    @bbox = {width: args.width, height: args.height}
    @size = @bbox
    @container_id = args.container_id

    # create stage
    @stage = new Kinetic.Stage(
      container: @container_id,
      width: @size.width, height: @size.height)
    @layer = new Kinetic.Layer()
    @stage.add(@layer)

    # selected points
    @points = []
    # KineticJS object for each point
    @k_points = []

    # set photo
    @update_photo(0)

    # mouse clicks
    @stage.on('click', =>
      @click(@stage.getMousePosition())
      @update_btn()
    )

    # clicked submit button
    btn_submit = =>
      # elapsed time
      @cur_photo.time_ms = @cur_photo.timer.time_ms()
      @cur_photo.time_active_ms = @cur_photo.timer.time_active_ms()

      # store points as string
      cur_points = []
      for p in @points
        cur_points.push(p.x / @size.width)
        cur_points.push(p.y / @size.height)
      @cur_photo.points = cur_points.join()

      # next photo or submit
      if @cur_idx < window.mt_photos.length - 1
        @update_photo(@cur_idx + 1)
      else
        btn_submit_ok()

    # submit button
    $('#btn-submit').on('click', =>
      if @points.length >= window.min_points
        btn_submit()
    )

    $('#btn-none').on('click', =>
      if @points.length >= window.min_points
        btn_submit()
      else
        message = ("<p>You have selected #{@points.length} white spot(s).  Are you sure that there are no more white or almost-white parts of image?</p>")
        window.show_modal_areyousure(
          label: "Are you sure?"
          message: message
          yes_text: "Yes, there are no white spots"
          no_text: "Nevermind"
          yes: btn_submit
        )
    )

  # show a photo index
  update_photo: (new_idx) ->
    $('#btn-submit').attr('disabled', 'disabled')
    $('#btn-none').attr('disabled', 'disabled')

    @cur_idx = new_idx
    @cur_photo = window.mt_photos[@cur_idx]

    if @k_photo?
      @k_photo.remove()
    @k_photo = null

    # reset points
    for p in @k_points
      p.remove()
    @k_points = []
    @points = []

    @add_loading()
    @photo_obj = new Image()
    @photo_obj.crossOrigin = ''
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
      @set_vertices(@vertices) if @vertices?
      @layer.draw()
      @cur_photo.timer = new ActiveTimer()
      @cur_photo.timer.start()
      @update_btn()
    @photo_obj.src = get_cors_url(@cur_photo.url)

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

  click: (p) ->
    if @k_loading? or not @k_photo
      console.log 'not loaded yet'
      return

    if @remove_point(p, 70)
      return

    # check for oversaturated pixels
    rgb = $('#' + @container_id)?.find('canvas')[0]?.getContext('2d')?.getImageData(p.x, p.y, 1, 1)?.data
    if rgb? and rgb[0] >= 253 and rgb[1] >= 253 and rgb[2] >= 253
      window.show_modal_error('Please avoid oversaturated spots.  Click on the Instructions button for more information.')
      return

    circle = new Kinetic.Circle(
      x: p.x, y: p.y, radius: 5,
      stroke: '#f00', fill: 'white',
      opacity: 0.7
    )

    @k_points.push(circle)
    @points.push(clone_pt(p))
    @layer.add(circle)
    @layer.draw()

  remove_point: (p, radius = 5) ->
    for q, i in @points
      if dist_pt(p, q) <= radius
        @remove_idx(i)
        return true
    return false

  remove_idx: (i) ->
    @points.remove(i)
    @k_points[i].remove()
    @k_points.remove(i)
    @layer.draw()

  update_btn: ->
    if @points.length >= window.min_points
      $('#btn-submit').removeAttr('disabled')
      $('#btn-none').attr('disabled', 'disabled')
    else
      $('#btn-submit').attr('disabled', 'disabled')
      $('#btn-none').removeAttr('disabled')
      $('#image-index').text(@cur_idx + 1)
