$('#content-container').on('click', '.action-show-reject', ->
  $(@).hide()
  $(@).parent('.admin-actions').find('.admin-actions-reject').show()
)

$('#content-container').on('click', '.action-review', ->
  window.show_modal_error('TODO')
  return

  parent = $(@).parent('.admin-actions')
  assignment_id = parent.attr('data-assignment')
  action = $(@).attr('data-action')
  message = parent.find(".feedback-#{action}").val()

  $.ajax(
    type: 'POST',
    url: window.location,
    dataType: 'json'
    data:
      assignment_id: assignment_id
      action: action
      message: message
    success: (data, status) ->
      if data.result == 'success'
        $(@).parent('.admin-actions').html("<p>Success</p>")
      else
        window.show_modal_error("Error contacting server (#{data})")
    error: ->
      window.show_modal_error("Error contacting server")
  )
)

$('#content-container').on('click', '.action-block', ->
  window.show_modal_error('TODO')
  return

  assignment_id = $(@).parent('.admin-actions').attr('data-assignment')
  message = parent.find(".feedback-reject").val()

  $.ajax(
    type: 'POST',
    url: window.location,
    dataType: 'json'
    data:
      assignment_id: assignment_id,
      action: 'block',
      message: message
    success: (data, status) ->
      if data.result == 'success'
        $(@).parent('.admin-actions').html("<p>Success</p>")
      else
        window.show_modal_error("Error contacting server (#{data})")
    error: ->
      window.show_modal_error("Error contacting server")
  )
)

$('#content-container').on('click', '.action-auto-approve', ->
  window.show_modal_error('TODO')
  return

  assignment_id = $(@).parent('.admin-actions').attr('data-assignment')
  message = parent.find(".feedback-approve").val()

  $.ajax(
    type: 'POST',
    url: window.location,
    dataType: 'json'
    data:
      assignment_id: assignment_id,
      action: 'auto-approve',
      message: message,
    success: (data, status) ->
      if data.result == 'success'
        $(@).parent('.admin-actions').html("<p>Success</p>")
      else
        window.show_modal_error("Error contacting server (#{data})")
    error: ->
      window.show_modal_error("Error contacting server")
  )
)
