# Handles submitting of tasks for mturk tasks
# Required scripts:
#   common/util.coffee
# Required templates:
#   modal_loading.html
#   modal_error.html

window.load_start = Date.now()
$(window).on('load', ->
  window.time_load_ms = +(Date.now() - window.load_start)
)

$( ->
  mt_submit_ready = false

  # Ready to submit with the provided data
  window.mt_submit_ready = (data_callback) ->
    if not mt_submit_ready
      mt_submit_ready = true
      btn = $('#btn-submit').removeAttr('disabled')
      if data_callback?
        btn.on('click', window.mt_submit(data_callback))

  # No longer ready to submit
  window.mt_submit_not_ready = (disable=true) ->
    if mt_submit_ready
      mt_submit_ready = false
      if disable then $('#btn-submit').attr('disabled', 'disabled').off('click')

  # Submit from javascript
  window.mt_submit = (data_callback) ->
    mt_submit_ready = true
    do_submit = mt_submit_impl(data_callback)

    if (window.ask_for_feedback == true and window.show_modal_feedback? and window.feedback_bonus?)
      window.show_modal_feedback(
        'Thank you!',
        ("<p>We will give a bonus of #{window.feedback_bonus} if you help us improve " +
        'the task and answer these questions.</p>' +
        '<p>If you don\'t want to answer, just click "Submit".</p>'),
        do_submit
      )
    else
      do_submit()

  # Submit a partially completed task
  window.mt_submit_partial = (data) ->
    console.log "partial submit data:"
    console.log data
    $.ajax(
      type: 'POST'
      url: window.location.href
      data: $.extend(true, {
        partial: true,
        screen_width: screen.width,
        screen_height: screen.height,
        time_load_ms: window.time_load_ms
      }, data)
      contentType: "application/x-www-form-urlencoded; charset=utf-8"
      dataType: 'json'
      success: (data, status, jqxhr) ->
        console.log "partial submit success: data:"
        console.log data
      error: ->
        console.log "partial submit error"
    )

  # tutorial is complete -- refresh to start the real task
  window.mt_tutorial_complete = ->
    window.show_modal_loading("Starting task...", 0)
    $.ajax(
      type: 'POST'
      url: window.location.href
      data: { tutorial_complete: true }
      dataType: 'json'
      success: (data, status, jqxhr) ->
        if data.result == "success"
          # change URL to avoid any caching
          new_url = window.location.href
          if new_url.indexOf('?') == -1
            new_url = new_url + '?tutorial_complete=true'
          else
            new_url = new_url + '&tutorial_complete=true'
          console.log "tutorial complete: redirecting to #{new_url}"
          window.location = new_url
          setInterval((-> window.location = new_url), 5000)
        else if data.result == "error"
          mt_submit_error("There was an error contacting the server; try again after a few seconds... (#{data.message})")
        else
          mt_submit_error("There was an error contacting the server; try again after a few seconds...")
      error: ->
        mt_submit_error("Could not connect to the server; try again after a few seconds...")
    )

  # ===== private methods =====

  mt_submit_error = (msg) ->
    hide_modal_loading( -> window.show_modal_error(msg) )

  mt_submit_impl = (data_callback) -> ->
    if not mt_submit_ready then return

    data = data_callback()
    feedback = window.get_modal_feedback?() if window.ask_for_feedback
    if feedback? and not $.isEmptyObject(feedback)
      data.feedback = JSON.stringify(feedback)

    console.log "submit data:"
    console.log data

    window.show_modal_loading("Submitting...", 0)
    $.ajax(
      type: 'POST'
      url: window.location.href
      data: $.extend(true, {
        screen_width: screen.width
        screen_height: screen.height
        time_load_ms: window.time_load_ms
      }, data)
      contentType: "application/x-www-form-urlencoded; charset=utf-8"
      dataType: 'json'
      success: (data, status, jqxhr) ->
        console.log "success: data:"
        console.log data

        host = window.getURLParameter('turkSubmitTo')
        console.log "host: #{host}"

        if data.result == "success"
          new_url = "#{host}/mturk/externalSubmit#{window.location.search}"
          console.log "success: redirecting to #{new_url}"
          window.location = new_url
          setInterval((-> window.location = new_url), 5000)
        else if data.result == "error"
          mt_submit_error("There was an error contacting the server; try submitting again after a few seconds... (#{data.message})")
        else
          mt_submit_error("There was an error contacting the server; try submitting again after a few seconds...")

      error: ->
        mt_submit_error("Could not connect to the server; try submitting again after a few seconds...")
    )
)
