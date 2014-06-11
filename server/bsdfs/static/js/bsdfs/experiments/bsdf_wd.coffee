to_hex = (d) ->
  h = Number(Math.floor(d)).toString(16)
  while h.length < 2
    h = '0' + h
  h

string_to_rgb = (str) ->
  r = parseInt(str.substring(1, 3), 16)
  g = parseInt(str.substring(3, 5), 16)
  b = parseInt(str.substring(5, 7), 16)
  return [r, g, b]

rgb_to_string = (rgb) ->
  return '#' + to_hex(rgb[0]) + to_hex(rgb[1]) + to_hex(rgb[2])

rand_int = (min, max) ->
    Math.floor(Math.random() * (max - min + 1)) + min

#rgb_to_normalized_color_str = (rgb) ->
  #scale = 255 / Math.max(rgb[0], rgb[1], rgb[2])
  #return rgb_to_string(rgb[0] * scale, rgb[1] * scale, rgb[2] * scale)

#normalize_color_str = (color_str) ->
  #rgb = string_to_rgb(color_str)
  #scale = 255 / Math.max(rgb[0], rgb[1], rgb[2])
  #return rgb_to_string(rgb[0] * scale, rgb[1] * scale, rgb[2] * scale)

#to_normalized_color = (color_string) ->
  #rgb = string_to_rgb(color_string)
  #max = Math.max(rgb[0], rgb[1], rgb[2])
  #if max == 0 then return '#000000'
  #return rgb_to_string(
    #rgb[0] * 255 / max,
    #rgb[1] * 255 / max,
    #rgb[2] * 255 / max
  #)

# mturk label bsdf - ward
class ShapeDisplay
  constructor: ->
    @k_stage = new Kinetic.Stage(
      container: 'shape-display',
      width: 300, height: 300)
    @k_layer = new Kinetic.Layer()
    @k_stage.add(@k_layer)

    sample_color = =>
      if not @mousedown then return
      p = @k_stage.getMousePosition()
      if not p? then return
      rgb = $('#shape-display').find('canvas')[0]?.getContext('2d')?.getImageData(p.x, p.y, 1, 1)?.data
      if not rgb? or rgb[3] != 255 then return
      console.log rgb
      color = rgb_to_string(rgb)
      console.log color
      window.set_color?(color)

    #@mousedown = false
    $('#shape-display').on('mousedown', (=> @mousedown = true; sample_color()))
    $('#shape-display').on('mouseup', => @mousedown = false)

    $('#shape-display').on('click mousemove', sample_color)

  set_shape: (s) ->
    console.log 'set_shape'
    console.log s
    show_image = =>
      if @k_image?
        @k_image.remove()
      dims = compute_dimensions(s, {width: 300, height:300})
      @k_image = new Kinetic.Image(
        x: 0, y: 0, image: s.img_square_300,
        width: dims.width, height: dims.height)
      @k_layer.add(@k_image)
      @k_layer.draw()
    show_image()
    $(s.img_square_300).load(show_image)

# disable text selection
$(document).on('selectstart', -> false)

# the corresponding loading_finish is at the end of the init
window.loading_start()

# default bsdf settings
window.update_mt_default = ->
  window.mt_default =
    type: 0
    type_str: 'nonmetal'
    color: '#555555'
    doi: rand_int(0, 15)
    contrast: Math.random()
window.update_mt_default()

# program state
mt_state =
  shapes: window.mt_contents
  idx: 0
  edit: 0
  cur: {
    shape_id: undefined
    type: mt_default.type
    type_str: mt_default.type_str
    doi: mt_default.doi
    color: mt_default.color
    constrast: mt_default.constrast
    edit: { type: 0, doi: 0, contrast: 0, color: false }
    give_up: false
    give_up_msg: ''
    timer: new ActiveTimer()
    time_ms: 0
    time_active_ms: 0
  }
  bsdfs: []

# true when loaded
window.colorpicker_ready = false

# appearance frame
app_frame = document.getElementById('frame-appearance').contentWindow

$( ->
  # toggle buttons
  $('.nav-tabs').button()

  # default material type
  $('#btn-bsdf-type' + mt_default.type).button('toggle')

  # appearance buttons
  $('#btn-bsdf-type0').on('click', ->
    $('#controls-contrast').show(400, -> window.colorpicker_update())
    mt_state.cur.type = 0
    mt_state.cur.type_str = 'nonmetal'
    mt_state.cur.edit.type += 1
    mt_state.cur.timer.ensure_started()
    mt_state.edit += 1
    app_frame?.updateType(0)
  )

  $('#btn-bsdf-type1').on('click', ->
    $('#controls-contrast').hide(400, -> window.colorpicker_update())
    mt_state.cur.type = 1
    mt_state.cur.type_str = 'metal'
    mt_state.cur.edit.type += 1
    mt_state.cur.timer.ensure_started()
    mt_state.edit += 1
    app_frame?.updateType(1)
  )

  # doi gloss slider
  $('#slider-doi').slider(
    value: mt_default.doi, min: 0, max: 15,
    slide: (event, ui) ->
      mt_state.cur.doi = ui.value
      mt_state.cur.edit.doi += 1
      mt_state.cur.timer.ensure_started()
      mt_state.edit += 1
      app_frame.updateAlpha?(15 - ui.value)
  )

  # contrast slider
  $('#slider-contrast').slider(
    value: mt_default.contrast * 1000, min: 0, max: 1000,
    slide: (event, ui) ->
      t = ui.value / 1000.0
      mt_state.cur.contrast = t
      mt_state.cur.edit.contrast += 1
      mt_state.cur.timer.ensure_started()
      mt_state.edit += 1
      app_frame.updateContrast?(t)
  )

  #$('#tonemap-scale').slider(
    #value: 1500, min: 0, max: 10000,
    #slide: (event, ui) -> app_frame.updateTonemapScale?(ui.value / 1000.0)
  #)
  #$('#tonemap-white').slider(
    #value: 4000, min: 0, max: 10000,
    #slide: (event, ui) -> app_frame.updateTonemapWhite?(ui.value / 1000.0)
  #)

  # fix iframe drag issue
  $('iframe').on('mouseover', ->
    $('.slider').trigger('mouseup')
  )

  # set initial color
  $('#frame-appearance').load(-> app_frame.updateColor(mt_default.color))

  # color picker
  window.colorpicker_default_color = mt_default.color
  Raphael( ->
    cp_offset = $("#colorpicker").offset()

    cp = Raphael.colorpicker(
      cp_offset.left, cp_offset.top,
      230, window.colorpicker_default_color, "colorpicker")

    cp_update =  ->
      cp_offset = $("#colorpicker").offset()
      cp.x = cp_offset.left
      cp.y = cp_offset.top

    cp.onchange = (clr) ->
      console.log('onchange ' + clr)
      mt_state.cur.color = clr
      mt_state.cur.edit.color += 1
      mt_state.cur.timer.ensure_started()
      mt_state.edit += 1
      app_frame?.updateColor?(clr)
      cp_update()

    $(window).resize(cp_update)

    # export methods
    window.colorpicker = cp
    window.colorpicker_update = cp_update
    window.colorpicker_ready = true
  )

  # start fetching images
  for s,i in mt_state.shapes
    s.img_square_300 = new Image()
    s.img_square_300.crossOrigin = ''
    s.photo.img = new Image()
    s.photo.img.crossOrigin = ''

    if i == 0
      window.loading_start()
      $(s.img_square_300).load(-> window.loading_finish())
      window.loading_start()
      $(s.photo.img).load( -> window.loading_finish())

    s.img_square_300.src = get_cors_url(s.url_square_300)
    s.photo.img.src = get_cors_url(s.photo.url)


  # submit button
  $('#btn-submit').on('click', btn_submit)

  # give-up button
  $('#btn-give-up').on('click', -> show_modal_give_up(
    'Give up',
    'Why are you giving up?  Please tell us your problem.',
    'Give me a new shape',
    ["The target image has more than one material.",
     "The target image is too small.",
     "I can't figure out what the target is.",
     "I don't understand how to do the task.",
     "It is not loading properly."]
  ))
  $('#modal-give-up-submit').on('click', ->
    mt_state.cur.give_up = true
    mt_state.cur.give_up_msg = $('#modal-give-up-text').val()
    btn_submit_ok()
  )

  # target shape tooltip
  $('#shape-display').tooltip(
    placement: 'bottom'
    title: 'Try and make the blob look it has the same substance as this image.  You can click here to set the color as well.'
  )

  # appearance tooltip
  $('#frame-appearance').tooltip(
    placement: 'bottom'
    title: 'Drag to rotate.  The rotation does not matter and is just to help see the blob appearance.'
  )

  # zoomed in view of context
  $('#photo-target').tooltip(
    placement: 'top'
    title: 'The target was cropped from this image (red shape).'
  )

  # last step: start first shape
  set_shape(0)

  # the corresponding loading_start is at the top of the script
  window.loading_finish()
)

btn_submit =  ->
  cur_edit = mt_state.cur.edit.type + mt_state.cur.edit.doi + mt_state.cur.edit.contrast + mt_state.cur.edit.color

  if mt_state.edit < 10
    window.show_modal_error(
      ("<p>It looks like you haven't adjusted the appearance!</p>" +
       "<p>Please try to do this HIT properly.</p>"),
      "Not so fast!"
    )
  else if cur_edit < 10
    message = ('<p>You did not change very much.  Please confirm that it looks like ' +
      'the two images have the same material/appearance.  The amount of blur in the ' +
      'reflection should also match.</p>' +
      "<div class='span3 thumbnail'><img src='#{mt_state.shapes[mt_state.idx].url_square_300}'/></div>" +
      "<div class='span3 thumbnail'><img id='areyousure-screenshot'/></div>")
    window.show_modal_areyousure(
      label: "Are you sure?"
      message: message
      before_show: -> $('#areyousure-screenshot').attr('src', app_frame.getScreenshot())
      yes_text: "Yes, they look the same"
      no_text: "Nevermind"
      yes: -> btn_submit_ok()
    )
  else
    btn_submit_ok()

btn_submit_ok = ->
  if mt_state.bsdfs.length < mt_state.shapes.length
    mt_state.cur.screenshot = app_frame.getScreenshot()
    mt_state.cur.time_ms = mt_state.cur.timer.time_ms()
    mt_state.cur.time_active_ms = mt_state.cur.timer.time_active_ms()
    mt_state.bsdfs.push($.extend(true, {}, mt_state.cur))
    console.log "mt_state:"
    console.log mt_state
    window.update_mt_default()

  if mt_state.idx == mt_state.shapes.length - 1
    # will call do_submit when user clicks button
    do_submit()
  else
    #window.mt_submit_partial(
    #  version: "1.0"
    #  bsdfs: JSON.stringify([mt_state.cur])
    #)
    set_shape(mt_state.idx + 1)

do_submit = ->
  results = {}
  time_ms = {}
  time_active_ms = {}
  for bsdf in mt_state.bsdfs
    results[bsdf.shape_id] = bsdf
    time_ms[bsdf.shape_id] = bsdf.time_ms
    time_active_ms[bsdf.shape_id] = bsdf.time_active_ms

  window.mt_submit( ->
      version: "1.0"
      results: JSON.stringify(results)
      time_ms: JSON.stringify(time_ms)
      time_active_ms: JSON.stringify(time_active_ms)
  )

window.set_color = (color) ->
  console.log "set_color(#{color})"
  mt_state.cur.color = color
  window.colorpicker_default_color = mt_state.cur.color
  if app_frame.updateColor?
    app_frame.updateColor?(mt_state.cur.color)
  else
    $('#frame-appearance').load( ->
      app_frame.updateColor(mt_state.cur.color)
    )
  if window.colorpicker_ready
    window.colorpicker_update()
    window.colorpicker.color(mt_state.cur.color)

set_shape = (idx) ->
  console.log("set_shape(#{idx})")
  s = mt_state.shapes[idx]

  # update state
  mt_state.idx = idx
  mt_state.cur.shape_id = s.id
  mt_state.cur.edit = { type: 0, doi: 0, contrast: 0, color: 0 }
  mt_state.cur.give_up = false
  mt_state.cur.give_up_msg = ''
  mt_state.cur.timer = new ActiveTimer()
  mt_state.cur.time_ms = null
  mt_state.cur.time_active_ms = null
  mt_state.cur.contrast = mt_default.contrast
  mt_state.cur.doi = mt_default.doi

  # update appearance iframe background
  if app_frame.updatePhoto?
    app_frame.updatePhoto(s.photo.url)
  else
    $('#frame-appearance').load( ->
      app_frame.updatePhoto(s.photo.url)
    )

  # reset contrast
  $('#slider-contrast').slider('value', mt_state.cur.contrast * 1000.0)
  if app_frame.updateContrast?
    app_frame.updateContrast(mt_state.cur.contrast)
  else
    $('#frame-appearance').load( ->
      app_frame.updateContrast(mt_state.cur.contrast)
    )
  $('#controls-contrast').show(400)

  # reset brightness
  $('#slider-doi').slider('value', mt_state.cur.doi)
  if app_frame.updateAlpha?
    app_frame.updateAlpha(15 - mt_state.cur.doi)
  else
    $('#frame-appearance').load( ->
      app_frame.updateAlpha(15 - mt_state.cur.doi)
    )

  # reset type
  if mt_state.cur.type != 0
    $('#btn-bsdf-type0').button('toggle')
    mt_state.cur.type = 0
    if app_frame.updateType?
      app_frame.updateType(mt_state.cur.type)
    else
      $('#frame-appearance').load( ->
        app_frame.updateType(mt_state.cur.type)
      )

  # set color
  if s.dominant_rgb0?
    mt_state.cur.color = s.dominant_rgb0
  else
    mt_state.cur.color = '#555555'
  window.set_color(mt_state.cur.color)

  # update context window
  $('.photo-target').hide()
  $("#photo-target-#{s.id}").show()

  # update shape target
  if not window.shape_display?
    window.shape_display = new ShapeDisplay()
  window.shape_display.set_shape(s)

  # update counter display
  $('#current-idx').text(idx + 1)
