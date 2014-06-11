## Common UI helpers

# Helper for hover items
$(document).on('mouseover', '.hover-toggle', ->
  out = $(@).find('.show-on-mouseout')
  over = $(@).find('.show-on-mouseover')
  w = out.width()
  h = out.height()
  out.hide()
  over.width(w)
  over.height(h)
  over.show()
)
$(document).on('mouseout', '.hover-toggle', ->
  $(@).find('.show-on-mouseout').show()
  $(@).find('.show-on-mouseover').hide()
)

# Speedup for categories pages
do ->
  handle_nav = (id) ->
    nav_div = $("div##{id}")
    if nav_div.length > 0
      data_spinner = nav_div.attr('data-spinner')
      if (not data_spinner?) or data_spinner == "true"
        nav_div.on('click', 'li > a', ->
          if $(@).attr('href') and not $(@).parent().hasClass('disabled')
            $('.loading-spinner').remove()
            $("div##{id} li.active").removeClass('active')
            $(@).closest('li').addClass('active')
            $(@).append(' <i class="icon-spinner icon-spin loading-spinner"></i>')
            timer = setTimeout(( =>
              $('div#content').html('<i class="icon-spinner icon-spin icon-2x"></i>')
            ), 1000)
            window.on('beforeunload', ->
              clearTimeout(timer)
              null
            )
        )

  handle_nav('subnav')
  handle_nav('sidenav')
