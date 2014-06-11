# Timer that stops counting when the user leaves the window
class ActiveTimer
  constructor: ->
    @started = false
    @total_start = null
    @active_start = null
    @partial_time_ms = 0

    $(window).on('focus', =>
      if @started
        @active_start = Date.now()
    )

    $(window).on('blur', =>
      if @started and @active_start?
        @partial_time_ms += Date.now() - @active_start
      @active_start = null
    )

  start: ->
    @total_start = Date.now()
    @active_start = Date.now()
    @partial_time_ms = 0
    @started = true

  ensure_started: ->
    if not @started then @start()

  time_ms: ->
    if @started
      Date.now() - @total_start
    else
      0

  time_active_ms: ->
    if @started
      if @active_start?
        @partial_time_ms + (Date.now() - @active_start)
      else
        @partial_time_ms
    else
      0
