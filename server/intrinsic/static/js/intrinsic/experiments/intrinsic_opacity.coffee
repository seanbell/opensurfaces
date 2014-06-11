$( ->
  # pre-load images
  image_urls = unique_array(
    p.photo.image['2048'] for p in window.mt_contents)

  # re-group points by photo, the new 'content' is one photo and its points
  photos_map = {}
  for url, i in image_urls
    photos_map[url] =
      photo:
        url: url
        obj: load_image(url)
      points: []
  for p in window.mt_contents
    photo = photos_map[p.photo.image['2048']]
    photo.points.push(p)
    p.opaque = true
    p.zoom = 1

  # start the experiment
  contents = (photo for url, photo of photos_map)
  experiment = new IntrinsicClassify(contents)
  experiment.set_idx(0)
)

class IntrinsicClassify
  constructor: (contents) ->
    @contents = contents
    @loading = true

    @submit_enabled = false
    @ui = new IntrinsicClassifyUI()

    $(window).on('resize', debounce(@on_resize))
    $('#mt-container').on('mousedown', @on_mousedown)
    $('#btn-back').on('click', @btn_back)
    $('#btn-next').on('click', @btn_next)
    $('#btn-submit').on('click', @btn_submit)
    $('#btn-reset').on('click', @btn_reset)
    $('#btn-zoom-in').on('click', @btn_zoom_in)
    $('#btn-zoom-out').on('click', @btn_zoom_out)

  set_idx: (idx) ->
    @cur_idx = idx
    @content = @contents[idx]
    @loading_start()
    load_image(@content.photo.url, @loading_finish)

  set_submit_enabled: (b) ->
    if b
      @ui.clear_ui()
      $('#mt-done').show()
    else
      $('#mt-done').hide()
    set_btn_enabled('#btn-submit', b)
    @submit_enabled = b

  start_timer: ->
    @timer = new ActiveTimer()
    @timer.start()

  stop_timer: ->
    time_ms = @timer.time_ms() / @content.points.length
    time_active_ms = @timer.time_active_ms() / @content.points.length
    for p in @content.points
      p.time_ms = time_ms
      p.time_active_ms = time_active_ms

  check_for_common_mistakes: (do_next) ->
    num_opaque = 0
    for p in @content.points
      if p.opaque
        num_opaque += 1

    if @content.points.length >= 2 and num_opaque == 0
      message = ('<p>You selected every point.  Are you sure ' +
        'that every point is transparent or on a mirror?</p>')
      window.show_modal_areyousure(
        label: "Are you sure?"
        message: message
        yes_text: "Yes, all points are transparent or on a mirror"
        no_text: "Nevermind"
        yes: do_next
      )
    else if @content.points.length >= 6 and num_opaque <= 2
      message = ('<p>You selected almost every point.  Are you ' +
        'sure that most points are transparent or on a mirror?</p>')
      window.show_modal_areyousure(
        label: "Are you sure?"
        message: message
        yes_text: "Yes, most points are transparent or on a mirror"
        no_text: "Nevermind"
        yes: do_next
      )
    else
      do_next?()

  on_mousedown: (e) =>
    if not @loading and not @submit_enabled
      p = @ui.get_point_from_click(@content, e)
      if p?
        p.opaque = not p.opaque
        p.zoom = @ui.get_zoom_scale()
        @ui.update_ui(@content)

    #console.log JSON.stringify(
      #photo: @content.photo.url
      #points: ({x: p.x, y: p.y} for p in @content.points)
      #opaque: (p.opaque for p in @content.points)
    #)
    return true

  on_resize: =>
    if not @loading and not @submit_enabled
      @ui.update_ui(@content)

  btn_reset: =>
    if not @loading and not @submit_enabled
      for p in @content.points
        p.opaque = true
      @ui.update_ui(@content)

  btn_back: =>
    if not @loading
      @set_submit_enabled(false)
      if @cur_idx >= 1
        @set_idx(@cur_idx - 1)

  btn_next: =>
    if not @loading and not @submit_enabled
      @stop_timer()
      @check_for_common_mistakes( =>
        if @cur_idx < @contents.length - 1
          @set_idx(@cur_idx + 1)
        else
          @cur_idx += 1
          set_btn_enabled('#btn-next', false)
          set_btn_enabled('#btn-back', true)
          set_btn_enabled('.btn-controls', false)
          @set_submit_enabled(true)
      )

  btn_zoom_in: =>
    if not @loading and not @submit_enabled
      @ui.zoom_in()

  btn_zoom_out: =>
    if not @loading and not @submit_enabled
      @ui.reset_zoom()

  loading_start: =>
    @loading = true
    window.show_modal_loading("Loading...", 250)
    set_btn_enabled('#btn-next', false)
    set_btn_enabled('#btn-back', false)
    set_btn_enabled('.btn-controls', false)
    @set_submit_enabled(false)

  loading_finish: =>
    $('#image-index').text(
      "Image #{@cur_idx + 1} of #{@contents.length}")
    window.hide_modal_loading()
    @ui.update_ui(@content, ( =>
      set_btn_enabled('#btn-next', true)
      set_btn_enabled('#btn-back', @cur_idx > 0)
      set_btn_enabled('.btn-controls', true)
      @start_timer()
      @loading = false
    ))

  btn_submit: =>
    if not @loading and @submit_enabled
      window.mt_submit( ->
        results = {}
        time_ms = {}
        time_active_ms = {}
        for c in window.mt_contents
          results[c.id] =
            opaque: c.opaque
            zoom: c.zoom
          time_ms[c.id] = c.time_ms
          time_active_ms[c.id] = c.time_active_ms

        version: '1.0'
        results: JSON.stringify(results)
        time_ms: JSON.stringify(time_ms)
        time_active_ms: JSON.stringify(time_active_ms)
      )
