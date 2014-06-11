class SearchRequest
  constructor: ->
    @aborted = false

  abort: ->
    if @timer?
      clearTimeout(@timer)
      @timer = null
    @xhr?.abort()
    @xhr = null
    @aborted = true

  start: ->
    clearTimeout(@timer) if @timer?
    @timer = setTimeout(@do_request, 50)

  do_request: =>
    url = window.location.href.split('?')[0]

    query = (
      $('#search-form').serialize() +
      '&planar=' +
        $('#group-planar').find('.active').attr('data-value') +
      '&whitebalanced=' +
        $('#group-whitebalanced').find('.active').attr('data-value') +
      '&contrast=' +
        $('#slider-contrast').slider('values', 0) + '-' +
        $('#slider-contrast').slider('values', 1) +
      '&doi=' +
        $('#slider-doi').slider('values', 0) + '-' +
        $('#slider-doi').slider('values', 1)
    )


    $('#results').empty()
    $('#results-loading').show()

    if not @aborted
      console.log("query: #{query}")
      @xhr = $.ajax(
        url: url
        type: 'POST'
        data: query
        success: (data) =>
          if not @aborted
            $('#results-loading').hide()
            $('#results').html(data)
            $('a.endless_more').attr('href', url + '?' + query + '&page=2')
            $(document).trigger("items-added")
      )

$( ->
  on_change = ->
    window.current_request?.abort()
    window.current_request = new SearchRequest()
    window.current_request.start()

  $('.combobox').combobox().on('change', on_change)
  $('.trigger-change').on('change', on_change)
  $('.trigger-click').on('click', on_change)

  $('#slider-contrast').slider(
    range: true, min: 0, max: 1, step: 0.01, values: [0, 1], change: on_change
  )
  $('#slider-doi').slider(
    range: true, min: 0, max: 15, values: [0, 15], change: on_change
  )

  $('input.combobox')
    .css('max-width', '60%')
    .css('margin-bottom', '0px')

  on_change()
)
