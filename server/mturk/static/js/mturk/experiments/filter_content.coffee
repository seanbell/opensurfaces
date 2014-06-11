window.num_selected = 0

$( ->
  for c in mt_contents
    c.selected = false
    c.canttell = false

  # remaining code only applies if in non-preview mode
  for c in window.mt_contents
    $("#entry-#{c.id}").on('click', do (c) -> ->
      c.selected = not c.selected
      if c.selected
        $(this).closest('.thumbnail').addClass('item-selected')
        $("#no-#{c.id}").hide()
        $("#yes-#{c.id}").show()
        window.num_selected += 1
        if c.canttell then $("#canttell-#{c.id}").trigger('click')
      else
        $(this).closest('.thumbnail').removeClass('item-selected')
        $("#no-#{c.id}").show()
        $("#yes-#{c.id}").hide()
        window.num_selected -= 1

      $("#num-selected").text(window.num_selected)
    )

    $("#canttell-#{c.id}").on('click', do (c) -> ->
      c.canttell = not c.canttell
      if c.canttell
        $(@).addClass('active')
        if c.selected then $("#entry-#{c.id}").trigger('click')
      else
        $(@).removeClass('active')
    )

  $('.entry').on('mouseover', -> $(this).find('.canttell').show())
  $('.entry').on('mouseout', -> $(this).find('.canttell').not('.active').hide())

  btn_submit =  ->
    if window.num_selected > 0
      btn_submit_ok()
    else
      message = ("<p>You have not selected any objects.</p>")
      window.show_modal_areyousure(
        label: "Are you sure?"
        message: message
        yes_text: "Yes, no objects match the instructions"
        no_text: "Nevermind"
        yes: -> btn_submit_ok()
      )

  btn_submit_ok = ->
    results = {}
    for c in window.mt_contents
      results[c.id] =
        selected: c.selected
        canttell: c.canttell
    time_ms = window.mt_timer.time_ms()
    time_active_ms = window.mt_timer.time_active_ms()

    window.mt_submit( ->
      version: "1.0"
      results: JSON.stringify(results)
      time_ms: time_ms
      time_active_ms: time_active_ms
    )

  window.mt_timer = new ActiveTimer()
  $(window).on('load', ->
    $('#btn-submit').removeAttr('disabled')
    $('#btn-submit').on('click', btn_submit)
    window.mt_timer.start()
  )
)
