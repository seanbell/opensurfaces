$( ->
  # pre-process points
  id = 0
  for c in window.mt_tut_contents
    for p in c.points
      if not p.opaque?
        p.opaque = true
      p.locked = false
      p.id = id
      id += 1
    if c.points_scale?
      for p in c.points
        p.x /= c.points_scale.x
        p.y /= c.points_scale.y
      delete c.points_scale
    if c.shown_opaque?
      for p, i in c.points
        p.opaque = c.shown_opaque[i]
      delete c.shown_opaque
    if c.expected_opaque?
      for p, i in c.points
        p.expected_opaque = c.expected_opaque[i]
    else
      for p in c.points
        p.locked = true
    kept_points = []
    for p in c.points
      if p.y > 0.15
        kept_points.push(p)
    c.points = kept_points

  # pre-process photos
  for c in window.mt_tut_contents
    c.photo =
      url: c.photo_url
      obj: load_image(c.photo_url)

  # start the tutorial
  tutorial = new IntrinsicClassifyTutorial(window.mt_tut_contents)
  start_idx = window.getURLParameter('start_idx')
  if start_idx?
    start_idx = parseInt(start_idx)
  else
    start_idx = 0
  tutorial.set_idx(start_idx)
)

class IntrinsicClassifyTutorial
  constructor: (contents) ->
    @contents = contents

    @loading = true
    @submit_enabled = false
    @showing_correct_message = false

    @ui = new IntrinsicClassifyUI()

    $(window).on('resize', debounce(@on_resize))
    $('#mt-container').on('mousedown', @on_mousedown)
    $('#btn-back').on('click', @btn_back)
    $('#btn-next').on('click', @btn_next)
    $('#btn-submit').on('click', @btn_submit)
    $('#btn-reset').on('click', @btn_reset)

  set_idx: (idx) ->
    @cur_idx = idx
    @content = @contents[idx]
    @loading_start()
    @showing_correct_message = false
    @content.message = @content.message_tut
    load_image(@content.photo.url, @loading_finish)

  loading_start: =>
    @loading = true
    window.show_modal_loading("Loading...", 250)
    set_btn_enabled('#btn-next', false)
    set_btn_enabled('#btn-reset', false)
    set_btn_enabled('#btn-back', false)
    @set_submit_enabled(false)

  loading_finish: =>
    window.hide_modal_loading()
    @ui.update_ui(@content, ( =>
      set_btn_enabled('#btn-next', true)
      set_btn_enabled('#btn-reset', true)
      set_btn_enabled('#btn-back', @cur_idx > 0)
      @loading = false
    ))

  set_submit_enabled: (b) ->
    if b
      @ui.clear_ui()
      $('#mt-done').show()
      $('#btn-submit').show()
      $('#btn-next').hide()
    else
      $('#mt-done').hide()
      $('#btn-submit').hide()
      $('#btn-next').show()
    set_btn_enabled('#btn-submit', b)
    @submit_enabled = b

  # check for errors and return whether errors were checked
  check_for_mistakes: () ->
    if @content.expected_opaque?
      correct = true
      for p in @content.points
        if p.opaque != p.expected_opaque
          p.tut_error = true
          correct = false
        else
          p.tut_error = false
      if correct
        @showing_correct_message = true
        @content.message = @content.message_correct
        @ui.update_ui(@content)
      else
        @content.message = @content.message_error
        @ui.reset_zoom()
        @ui.update_ui(@content)
      return true
    return false

  on_resize: =>
    if not @loading and not @submit_enabled
      @ui.update_ui(@content)

  btn_submit: =>
    if @submit_enabled
      window.mt_tutorial_complete()

  btn_back: =>
    if not @loading
      @set_submit_enabled(false)
      if @cur_idx >= 1
        @set_idx(@cur_idx - 1)

  on_mousedown: (e) =>
    if not @loading and not @submit_enabled
      p = @ui.get_point_from_click(@content, e)
      if p? and not p.locked
        p.opaque = not p.opaque
        for q in @content.points
          q.tut_error = false
        @ui.update_ui(@content)

  btn_next: =>
    if @showing_correct_message or not @check_for_mistakes()
      if @cur_idx < @contents.length - 1
        @set_idx(@cur_idx + 1)
      else
        @cur_idx += 1
        set_btn_enabled('#btn-next', false)
        set_btn_enabled('#btn-back', true)
        @set_submit_enabled(true)
