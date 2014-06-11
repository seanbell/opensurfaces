$(document).on('click', '.example-label', ->
  $t = $(@)
  id = $t.attr('data-id')
  good = $t.attr('data-good')
  console.log "#{id}: was #{good}"

  $.ajax('/mturk/admin/example/ajax/',
    type: 'POST'
    data:
      id: id
      good: if good == "True" then "False" else "True"
    success: =>
      if good == 'True'
        $t.attr('data-good', 'False')
        $t.find('.label-success').hide()
        $t.find('.label-important').show()
      else
        $t.attr('data-good', 'True')
        $t.find('.label-success').show()
        $t.find('.label-important').hide()
      console.log 'toggle: success'
    error: =>
      window.show_modal_error("Could not contact server")
      console.log 'toggle: error'
  )
)
