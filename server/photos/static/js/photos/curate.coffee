$( ->
  $('.entry > a').on('click', ->
    $(@).parent().find('.curate-buttons').toggle()
    return false
  )

  $('.curate-buttons > .btn').on('click', ->
    photo_id = $(@).closest('.entry').attr('data-id')
    attr = $(@).attr('data-attr')
    val = not $(@).hasClass('active')
    data =
      action: 'button'
      attr: attr
      val: val
      photo_id: photo_id
    $.ajax(
      type: 'POST'
      url: window.location
      data: data
      success: (data) =>
        console.log 'success:', data
        if data.photo_id == photo_id and data.attr == attr
          if data.val
            $(@).addClass('active')
          else
            $(@).removeClass('active')
        else
          alert 'error -- see console log'
      error: (data) ->
        console.log 'data:', data
        console.log 'error:', data
        alert 'error -- see console log'
    )
  )

  $('#btn-done').on('click', ->
    items = []
    $('.entry').each( ->
      updates = {}
      console.log $(@).find('.btn')
      $(@).find('.btn').each( ->
        updates[$(@).attr('data-attr')] = $(@).hasClass('active')
        true
      )
      items.push(
        photo_id: $(@).attr('data-id')
        updates: updates
      )
      true
    )

    console.log items
    $.ajax(
      type: 'POST'
      url: window.location
      data:
        action: 'done'
        items: JSON.stringify(items)
      success: (data) ->
        window.location.reload()
      error: (data) ->
        console.log 'data:', data
        console.log 'error:', data
        alert 'error -- see console log'
    )
  )
)
