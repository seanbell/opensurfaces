#
# ENDLESS PAGINATION
#

$ ->
  $("a.endless_more").live("click", ->
    container = $(this).closest(".endless_container")
    get_url = $(this).attr("href")
    $(this).remove()

    container.find(".endless_loading").show()
    get_data = "querystring_key=" + $(this).attr("rel").split(" ")[0]
    $.get(get_url, get_data, (data) ->
      container.before(data)
      container.remove()
      $(document).trigger("items-added")
    )
    false
  )

  $("a.endless_page_link").live("click", ->
    page_template = $(this).closest(".endless_page_template")
    if not page_template.hasClass("endless_page_skip")
      data = "querystring_key=" + $(this).attr("rel").split(" ")[0]
      page_template.load $(this).attr("href"), data
      false
  )

  on_scroll = ->
    delta = $(document).height() - $(window).height() - $(window).scrollTop()
    if delta <= 3200 then $("a.endless_more").click()
  $(window).on('scroll', on_scroll)
  on_scroll()
  setTimeout((-> $("a.endless_more").click()), 1000)


#
# SUBNAV
#

$ ->
  isFixed = false
  $nav = $("#subnav")
  if not $nav.length then return
  navTop = $nav.offset().top - $(".navbar").first().height() - 20
  on_scroll = ->
    $after = $("#subnav-after")
    scrollTop = $(window).scrollTop()
    if scrollTop >= navTop and not isFixed
      isFixed = true
      $nav.addClass("subnav-fixed")
      $after.addClass("subnav-after-fixed")
    else if scrollTop <= navTop and isFixed
      isFixed = false
      $nav.removeClass("subnav-fixed")
      $after.removeClass("subnav-after-fixed")
  $(window).on("scroll", on_scroll)
  on_scroll()

#
# TOOLTIPS, POPOVERS, HOVERS, ETC
#

$ ->
  on_items_added = ->
    $(".nav-tabs").button()
    $(".tool").removeClass("tool").tooltip(
      placement: "bottom"
      trigger: "hover"
    )
    $(".pop").removeClass("pop").popover(
      placement: "bottom"
      trigger: "hover"
    )
  $(document).on("items-added", on_items_added)
  on_items_added()

  $("body").delegate(".entry-thumb", "mouseover", ->
    $(this).addClass "entry-thumb-hover"
  ).delegate(".entry-thumb", "mouseout", ->
    $(this).removeClass "entry-thumb-hover"
  )
