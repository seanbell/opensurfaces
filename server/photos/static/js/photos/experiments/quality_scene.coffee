window.num_selected = 0

$( ->
  for c in window.mt_photos
    c.selected = false
    $("#thumbnail-#{c.id}").on('click', do (c) -> ->
      if not c.display?.is_loading()
        c.selected = not c.selected
        if c.selected
          $(this).addClass('item-selected')
          $not = $("#not-#{c.id}")
          $not.hide()
          $not.parent().parent().css('background-color', '#fff1c5')
          window.num_selected += 1
        else
          $(this).removeClass('item-selected')
          $not = $("#not-#{c.id}")
          $not.show()
          $not.parent().parent().css('background-color', '')
          window.num_selected -= 1

        $("#num-selected").text(window.num_selected)
      )
)

btn_submit = ->
  if window.num_selected > 0
    btn_submit_ok()
  else
    message = ("<p>You have not selected any images.  Are you sure that no images match their category?</p>")
    window.show_modal_areyousure(
      label: "Are you sure?"
      message: message
      yes_text: "Yes, all the categories are wrong"
      no_text: "Nevermind"
      yes: btn_submit_ok
    )

btn_submit_ok = ->
  time_ms = window.mt_timer.time_ms()
  time_active_ms = window.mt_timer.time_active_ms()
  window.mt_submit( ->
    results = {}
    for c in window.mt_photos
      results[c.id] = c.selected

    version: '1.0'
    results: JSON.stringify(results)
    time_ms: JSON.stringify(time_ms)
    time_active_ms: JSON.stringify(time_active_ms)
  )

# wait for images to load before allowing submit
window.mt_timer = new ActiveTimer()
$(window).on('load', ->
  $('#btn-submit').on('click', btn_submit)
  window.mt_timer.start()
  $('#btn-submit').removeAttr('disabled')
)
