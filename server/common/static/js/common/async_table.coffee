$( ->
  table_attempt = 0

  # update the data after loading
  update_table = (callback) ->
    table_attempt += 1
    url = "#{window.table_url}?attempt=#{table_attempt}"
    console.log "updating table... (#{url})"
    $.ajax(url,
      type: 'GET'
      cache: false
      timeout: 600000 # 10 min timeout
      success: (data) ->
        console.log 'success'
        $('#table').html(data)
        callback?()
      error: (data) ->
        console.log 'error', data
        callback?()
    )

  # continue checking for new table data
  check_table = ->
    if $('#table > .progress').length > 0
      console.log 'sleep 10 seconds...'
      setTimeout((-> update_table(check_table)), 10000)
    else
      console.log 'table loaded'

  update_table(check_table)
)
