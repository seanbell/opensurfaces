$( ->
  console.log("Window loaded")
  # temporary UI for initialization
  ui = new IntrinsicCompareUI()

  # preload images and preprocess points
  console.log("Prefetch images...")
  for c in window.mt_contents
    c.zoom_delay = 1000
    if not c.photo.obj?
      c.photo.url = c.photo.image['2048']
      c.photo.obj = load_image(c.photo.url)

    c.points = [
      {
        x_orig: c.point1.x,
        y_orig: c.point1.y,
        label: "1",
        color:'#700'
      }, {
        x_orig: c.point2.x,
        y_orig: c.point2.y,
        label: "2",
        color:'#007'
      }
    ]

    # guess the zoom size before loading image
    c.z_guess = ui.compute_target_zoom([
      [c.point1.x * 2048, c.point1.y * 2048 / c.photo.aspect_ratio],
      [c.point2.x * 2048, c.point2.y * 2048 / c.photo.aspect_ratio],
    ])

  # time spent zooming between the two targets
  interpolation_time = (c1, c2) ->
    if c1.photo.url != c2.photo.url
      return Number.POSITIVE_INFINITY
    return d3.interpolateZoom(c1.z_guess, c2.z_guess).duration

  # re-order to minimize zoom time
  console.log("Re-ordering points...")
  if window.mt_contents.length > 0
    contents = window.mt_contents[..]
    sorted_contents = []
    while contents.length > 0
      if sorted_contents.length > 0
        c = sorted_contents[sorted_contents.length - 1]
      else
        c =
          z_guess: [ui.width / 2, ui.height / 2, ui.width]
          photo: contents[0].photo
      imin = 0
      dmin = Number.POSITIVE_INFINITY
      for i in [0..contents.length-1]
        d = interpolation_time(c, contents[i])
        if d < dmin
          dmin = d
          imin = i
      sorted_contents.push(contents[imin])
      contents.remove(imin)
    window.mt_contents = sorted_contents

  # start the task
  console.log("UI Constructor")
  experiment = new IntrinsicCompare()
  console.log("Start the task!")
  experiment.set_idx(0)
)


class IntrinsicCompare
  constructor: ->
    @loading = true
    @set_submit_enabled(false)
    @ui = new IntrinsicCompareUI()

    $(window).on('resize', debounce(@on_resize))
    $('.response-darker').on('click', @btn_response_darker)
    $('.response-confidence').on('click', @btn_response_confidence)
    $('#btn-highlight').on('click', @btn_highlight)
    $('#btn-zoom-out').on('click', @btn_zoom_out)
    $('#btn-back').on('click', @btn_back)
    $('#btn-submit').on('click', @btn_submit)
    $(window).on('keydown', @keydown)

  set_idx: (idx) ->
    console.log("set_idx(#{idx})")
    $('#mt-done').hide()
    @cur_idx = idx
    @content = window.mt_contents[@cur_idx]
    @loading_start()
    load_image(@content.photo.url, @loading_finish)

  set_submit_enabled: (b) ->
    set_btn_enabled('#btn-submit', b)
    @submit_enabled = b

  loading_start: =>
    @loading = true
    window.show_modal_loading("Loading...", 250)
    set_btn_enabled('button.response', false)
    set_btn_enabled('#btn-highlight', false)
    set_btn_enabled('#btn-zoom-out', false)
    set_btn_enabled('#btn-back', false)

  loading_finish: =>
    window.hide_modal_loading()
    $('#image-index').text(
      "Pair #{@cur_idx + 1} of #{window.mt_contents.length}")
    @ui.update_ui(@content, ( =>
      set_btn_enabled('button.response-darker', true)
      set_btn_enabled('button.response-confidence', false)
      set_btn_enabled('#btn-highlight', true)
      set_btn_enabled('#btn-zoom-out', true)
      set_btn_enabled('#btn-back', @cur_idx > 0)
      $('button.response-darker').removeClass('active')
      @timer = new ActiveTimer()
      @timer.start()
      @loading = false
    ))

  on_resize: =>
    if not @loading and not @submit_enabled
      @ui.update_ui(@content)

  keydown: (event) =>
    # (modals have the class 'in' when visible)
    if not $('.modal').hasClass('in')
      c = String.fromCharCode(event.which).toUpperCase()
      if @submit_enabled and event.which == 13
        $('#btn-submit').trigger('click')
      else if not @loading and c == 'B'
        $('#btn-back').trigger('click')
      else if not @loading and c == 'I'
        $('#btn-instructions').trigger('click')
      else if not @loading and not @submit_enabled
        if c == 'H'
          $('#btn-highlight').trigger('click')
        else if c == 'Z'
          $('#btn-zoom-out').trigger('click')
        else if c in ['1', '2', 'S', 'G', 'P', 'D']
          $("#btn-#{c}").trigger('click')
    true

  btn_zoom_out: =>
    if not @loading and not @submit_enabled
      #target = @ui.compute_current_zoom()
      #target[2] *= 4
      #if target[2] >= @ui.width
      target = [@ui.width / 2, @ui.height / 2, @ui.width]
      @ui.zoom_to_target(target)

  btn_highlight: =>
    if not @loading and not @submit_enabled
      @ui.highlight(@content)

  btn_back: =>
    if not @loading
      @set_submit_enabled(false)
      if @cur_idx >= 1
        @set_idx(@cur_idx - 1)

  btn_response_darker: (event) =>
    if not @loading
      @content.darker = $(event.target).attr('data-darker')
      set_btn_enabled('button.response-confidence', true)

  btn_response_confidence: (event) =>
    if not @loading and @content.darker?
      @content.time_ms = @timer.time_ms()
      @content.time_active_ms = @timer.time_active_ms()
      @content.confidence = $(event.target).attr('data-confidence')
      set_btn_enabled('button.response-confidence', false)

      # next content or allow submit
      if @cur_idx < window.mt_contents.length - 1
        @set_idx(@cur_idx + 1)
      else
        @cur_idx += 1
        set_btn_enabled('button.response', false)
        set_btn_enabled('#btn-highlight', false)
        set_btn_enabled('#btn-zoom-out', false)
        set_btn_enabled('#btn-back', true)
        @ui.clear_ui()
        $('#mt-done').show()
        @set_submit_enabled(true)

  btn_submit: =>
    if not @loading and @submit_enabled
      window.mt_submit( ->
        results = {}
        time_ms = {}
        time_active_ms = {}
        for c in window.mt_contents
          results[c.id] =
            darker: c.darker
            confidence: c.confidence
          time_ms[c.id] = c.time_ms
          time_active_ms[c.id] = c.time_active_ms

        version: '1.0'
        results: JSON.stringify(results)
        time_ms: JSON.stringify(time_ms)
        time_active_ms: JSON.stringify(time_active_ms)
      )
