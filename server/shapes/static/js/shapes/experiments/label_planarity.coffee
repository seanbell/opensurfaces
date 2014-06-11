$( ->
  window.num_selected = 0

  for c in window.mt_shapes
    c.display = new PolyDisplayFill(
      width: 450, height: 450,
      container_id: "canvas-#{c.shape.id}"
      photo_url: c.photo.url,
      vertices: c.shape.vertices
      triangles: c.shape.triangles
      segments: c.shape.segments
    )

    $("#thumbnail-#{c.shape.id}").on('click', do (c) -> ->
      if not c.display?.is_loading()
        c.selected = not c.selected
        if c.selected
          $(this).addClass('item-selected')
          $not = $("#not-#{c.shape.id}")
          $not.hide()
          $not.parent().parent().css('background-color', '#fff1c5')
          window.num_selected += 1
        else
          $(this).removeClass('item-selected')
          $not = $("#not-#{c.shape.id}")
          $not.show()
          $not.parent().parent().css('background-color', '')
          window.num_selected -= 1

        $("#num-selected").text(window.num_selected)
    )
)

btn_submit =  ->
  if window.num_selected > 0
    btn_submit_ok()
  else
    message = ("<p>You have not labeled all the images.</p>")
    window.show_modal_areyousure(
      label: "Are you sure?"
      message: message
      yes_text: "Yes, there are no flat shapes"
      no_text: "Nevermind"
      yes: -> btn_submit_ok()
    )

btn_submit_ok = ->
  results = {}
  for c in window.mt_shapes
    results[c.shape.id] = c.selected
  time_ms = +(Date.now() - window.start_time)

  window.mt_submit( ->
    version: "1.0"
    results: JSON.stringify(results)
    time_ms: time_ms
  )

$(window).on('load', ->
  window.start_time = Date.now()
  $('#btn-submit').on('click', btn_submit)
)

