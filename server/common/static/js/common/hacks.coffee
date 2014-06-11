## BROWSER HACKS

# Browser: IE
# Problem: doesn't implement vector-effect: non-scaling-stroke
# Hack solution: replace with stroke-width: 0.2%
if $.browser.msie
  console.log 'detected: IE'
  do ->
    fix_ie = ->
      $('.nss').css('vector-effect', '') \
        .css('stroke-width', '0.2%') \
        .css('stroke-linecap', 'round')
    fix_ie()
    $(document).on('items-added', fix_ie)
  if Number($.browser.version) < 10
    $('#outdated-browser-alert').show()

# Browser: Firefox and IE
# Problem: inline SVG height doesn't scale properly
# Hack solution: store aspect in tag and manually enforce aspect ratio
if not ($.browser.webkit or $.browser.opera)
  fix_aspect = ->
    $('svg.fix-aspect').each( ->
      t = $(this)
      aspect = t.attr('data-aspect')
      #console.log aspect
      if aspect?
        t.height(t.width() / aspect)
    )
  fix_aspect()
  $(document).on('items-added', fix_aspect)
  $(window).on('resize', fix_aspect)

# to show if not webkit
if not $.browser.webkit
  $('.if-not-webkit').show()
