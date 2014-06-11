window.photos = [
  {key: 'adelson', width: 1078, height: 838},
  {key: '176', width: 2048, height: 1360},
  {key: '835', width: 2048, height: 1362},
  {key: '103703', width: 2048, height: 1371},
  {key: '98082', width: 2048, height: 1360},
  {key: '66', width: 2048, height: 1356}
  {key: '104550', width: 2048, height: 1365}
  {key: '108505', width: 2048, height: 3072}
]

window.build_content = (c) ->
  ret = $.extend({}, c)
  if c.image_key?
    ret.photo = window.photos_by_key[c.image_key]
  if c.x1? and c.x1? and c.x2? and c.y2?
    ret.points = [
      {
        x_orig: c.x1 / ret.photo.width,
        y_orig: c.y1 / ret.photo.height,
        label: "1",
        color:'#700'
      }, {
        x_orig: c.x2 / ret.photo.width,
        y_orig: c.y2 / ret.photo.height,
        label: "2",
        color:'#007'
      }
    ]
  return ret

$( ->
  window.show_modal_loading("Loading...", 250)

  # load images
  for p in window.photos
    p.url = "/static/img/intrinsic/experiments/#{p.key}.jpg"
  image_urls = (p.url for p in window.photos)
  image_objs = load_images(image_urls, ->
    # store photo object
    for p, i in window.photos
      p.obj = image_objs[i]

    # index by key
    window.photos_by_key = {}
    for p in window.photos
      window.photos_by_key[p.key] = p

    # start the tutorial
    window.hide_modal_loading()
    tutorial = new IntrinsicCompareTutorial()
    start_idx = window.getURLParameter('start_idx')
    if start_idx?
      start_idx = parseInt(start_idx)
    else
      start_idx = 0
    tutorial.show_page(start_idx)
  )
)

class IntrinsicCompareTutorial
  constructor: ->
    @animating = true
    @set_submit_enabled(false)

    @ui = new IntrinsicCompareUI()
    @ui.extra_margin = 100

    @tutorial_content = [
      window.build_content(
        image_key: 'adelson',
        x1: 300, y1: 838/2, x2: 900, y2: 838/2,
        message: [
          'This short tutorial will teach you how to do this HIT.  You get as',
          'many tries as you like, and you don\'t have to do it again once',
          'you pass.  Click "Next" to continue to the next screen.'
        ]
      ),
      window.build_content(
        image_key: 'adelson',
        x1: 359, y1: 334, x2: 426, y2: 259,
        message: [
          'On this checkerboard pattern, there are two colors.',
          'Point 1 is on a dark square, and point 2 is on a light square.'
          'You can drag the photo to see more or scroll to zoom in/out.'
        ]
      ),
      window.build_content(
        image_key: 'adelson',
        x1: 359, y1: 334, x2: 621, y2: 454,
        message: [
          'Now, point 2 is in shadow.  However, we understand that the square',
          'at point 2 is still lighter than point 1.',
          '(Note that we are referring to the center of the circle)' ]
      ),
      window.build_content(
        image_key: '176',
        x1: 922, y1: 56, x2: 1041, y2: 279,
        message: [
          'In this photo, all points on the ceiling have the same surface',
          'color.  The surface is white even though shadows make some parts',
          'appear darker.' ]
      ),
      window.build_content(
        image_key: '176',
        x1: 602, y1: 550, x2: 1254, y2: 652,
        message: [
          'Similarly, these two points on the wall have the same color.',
          'The surface color is what matters, not the lighting or shadows.', ]
      ),
      window.build_content(
        image_key: '176',
        x1: 775, y1: 991, x2: 1002, y2: 906,
        message: [
          'The surface color at point 2 is darker than the surface color at',
          'point 1 even though it is under a highlight.' ]
      ),
      window.build_content(
        image_key: '176',
        x1: 1273, y1: 614, x2: 1368, y2: 641,
        expected_darker: ['E'],
        message: [
          'Now it is your turn.  Using the buttons at the top, indicate which',
          'point has a darker surface color.' ]
        message_darker_error: [
          'Try again.  Indicate which point has a darker surface color.' ]
        message_success: [
          'Correct!  Both points are on the same colored wall.' ]
      ),
      window.build_content(
        image_key: '66',
        x1: 211, y1: 862, x2: 390, y2: 827,
        message: [
          'Sometimes you cannot see enough and need to zoom out.' ]
      ),
      window.build_content(
        image_key: '66',
        x1: 211, y1: 862, x2: 390, y2: 827,
        zoom_out: true,
        message: [
          'You can do this with the scroll wheel.  You can also drag',
          'with the mouse.' ]
      ),
      window.build_content(
        image_key: '108505',
        x1: 1920, y1: 846, x2: 1440, y2: 732,
        expected_darker: ['E'],
        message: [
          'Using the buttons at the top, indicate which',
          'point has a darker surface color.' ]
        message_darker_error: [
          'Try again.  Remember that the point of this task is to ignore',
          'shading effects.  Imagine what it would look like if every',
          'surface was receiving the same amount of lighting.'
        ]
        message_success: [
          'Correct!  Both points are on a white colored wall.' ]
      ),
      window.build_content(
        image_key: '108505',
        x1: 1086, y1: 240, x2: 1077, y2: 573,
        expected_darker: ['E'],
        message: [
          'Using the buttons at the top, indicate which',
          'point has a darker surface color.' ]
        message_darker_error: [
          'Try again.  Remember that the point of this task is to ignore',
          'shading effects.  Imagine what it would look like if every',
          'surface was receiving the same amount of lighting.'
        ]
        message_success: [
          'Correct!  Both points are on a white colored wall.' ]
      ),
      window.build_content(
        image_key: '108505',
        x1: 1722, y1: 3030, x2: 1755, y2: 2670,
        expected_darker: ['1'],
        message: [
          'Using the buttons at the top, indicate which',
          'point has a darker surface color.' ]
        message_darker_error: [
          'Try again.  Remember that the point of this task is to ignore',
          'shading effects.' ]
        message_success: [
          'Correct!  The glossy floor is darker than the white wall.' ]
      ),
      window.build_content(
        image_key: '176',
        x1: 968, y1: 1100, x2: 1076, y2: 1163,
        expected_darker: ['2'],
        expected_confidence: ['1', '2'],
        message: [
          'Using the buttons at the top, indicate which point has a darker',
          'surface color.  Also indicate how confident you are.'
        ]
        message_darker_error: [
          'Try again.  They are close, but the strips of wood are not all',
          'the same color.' ]
        message_confidence_error: [
          'You should be able to tell with higher confidence.  Try zooming',
          'out (with the scroll wheel) or dragging the image around to see',
          'more.' ]
        message_success: [
          'Correct!  The two points are on slightly different colored',
          'strips of wood.' ]
      ),
      window.build_content(
        image_key: '103703',
        x1: 1637, y1: 587, x2: 1684, y2: 1123,
        message: [
          'Sometimes the image is too dark or bright and you cannot tell which',
          'point is darker.  In these cases, you can guess and then tell us',
          'that you are guessing.' ]
      ),
      window.build_content(
        image_key: '176',
        x1: 204, y1: 291, x2: 374, y2: 602,
        expected_darker: ['1', '2', 'E'],
        expected_confidence: ['0'],
        message: [
          'Using the buttons at the top, indicate which point has a darker',
          'surface color.  Also indicate how confident you are.' ]
        message_darker_error: [
          'This example is unclear, so click on any button.' ]
        message_confidence_error: [
          'This part of the image is too bright and washed out, so you cannot',
          'tell what the answer should be.  Therefore, you are only guessing'
          'and should tell us this.' ]
        message_success: [
          'Correct!  When the pixels are too bright or too dark to tell,',
          'please tell us that you are guessing.']
      )
      window.build_content(
        image_key: '835',
        x1: 446, y1: 1179, x2: 649, y2: 1112,
        expected_darker: ['1'],
        expected_confidence: ['1', '2'],
        message: [
          'Using the buttons at the top, indicate which point has a darker',
          'surface color.  Also indicate how confident you are.' ]
        message_darker_error: [
          'Try again.  Remember that you should try and ignore highlights.' ]
        message_confidence_error: [
          'You should be able to tell that the floor is darker',
          'than the carpet.  You can zoom out to better see.'
        ]
        message_success: [
          'Correct!  We care about intrinsic surface color, not highlights',
          'or shadows.'
        ]
      )
      window.build_content(
        image_key: '835',
        x1: 428, y1: 176, x2: 499, y2: 140,
        expected_darker: ['E'],
        expected_confidence: ['1', '2'],
        message: [
          'Using the buttons at the top, indicate which point has a darker',
          'surface color.  Also indicate how confident you are.' ]
        message_darker_error: [
          'Try again.  Remember that you should try and ignore highlights.' ]
        message_confidence_error: [
          'You should be able to tell that the two points are on the same wall.'
        ]
        message_success: [
          'Correct!  If two points have the same surface color, but one',
          'appears brighter because of a highlight, you should still consider',
          'them to have the same brightness.'
        ]
      )
      window.build_content(
        image_key: '66',
        x1: 331, y1: 1170, x2: 449, y2: 1203,
        expected_darker: ['E'],
        expected_confidence: ['1', '2'],
        message: [
          'Using the buttons at the top, indicate which point has a darker',
          'surface color.  Also indicate how confident you are.' ]
        message_darker_error: [
          'Try again.  Remember that you should try and ignore shadows.' ]
        message_confidence_error: [
          'You should be able to tell that the two points are on the same wall.'
        ]
        message_success: [
          'Correct!  If two points have the same surface color, but one',
          'appears darker because of a shadow, you should still consider',
          'them to have the same brightness.'
        ]
      )
      window.build_content(
        image_key: '835',
        x1: 1730, y1: 769, x2: 1629, y2: 965,
        expected_darker: ['1'],
        expected_confidence: ['1', '2'],
        message: [
          'Using the buttons at the top, indicate which point has a darker',
          'surface color.  Also indicate how confident you are.',
          '(Remember that you can drag or scroll to see more)',
        ]
        message_darker_error: [
          'Try again.  They are close, but one is slightly darker.',
          'You can see more of the carpet if you zoom out.'
        ]
        message_confidence_error: [
          'You should be able to tell with more accuracy than just guessing.',
          'Try zooming out or dragging the image to see more areas.' ]
        message_success: [
          'Correct!  The carpet is lighter even though it is in shadow.' ]
      )
      #window.build_content(
        #image_key: '98082',
        #x1: 867, y1: 564, x2: 1475, y2: 751,
        #expected_darker: ['2'],
        #expected_confidence: ['1', '2'],
        #message: [
          #'Using the buttons at the top, indicate which point has a darker',
          #'surface color.  Also indicate how confident you are.',
        #]
        #message_darker_error: [
          #'Try again.  They are close, but one is slightly darker.' ]
        #message_confidence_error: [
          #'You should be able to tell with more accuracy than just guessing.',
          #'Try zooming out or dragging the image to see more areas.' ]
        #message_success: [
          #'Correct!  It is a single material, but point 2 is on a darker'
          #'portion.' ]
      #),
      #window.build_content(
        #image_key: '98082',
        #x1: 1475, y1: 751, x2: 687, y2: 753,
        #expected_darker: ['E'],
        #expected_confidence: ['1', '2'],
        #message: [
          #'Using the buttons at the top, indicate which point has a darker',
          #'surface color.  Also indicate how confident you are.',
        #]
        #message_darker_error: [
          #'Try again.  Notice that the pattern is repeating.' ]
        #message_confidence_error: [
          #'You should be able to tell with more accuracy than just guessing.',
          #'Try zooming out or dragging the image to see more areas.' ]
        #message_success: [
          #'Correct!  The two points are on the same portion of a repeating',
          #'pattern.' ]
      #),
      window.build_content(
        image_key: '98082',
        x1: 129, y1: 476, x2: 508, y2: 349,
        expected_darker: ['E'],
        expected_confidence: ['1', '2'],
        message: [
          'Using the buttons at the top, indicate which point has a darker',
          'surface color.  Also indicate how confident you are.',
        ]
        message_darker_error: [
          'Try again.  You should ignore glossy highlights.' ]
        message_confidence_error: [
          'You should be able to tell with more accuracy than just guessing.',
          'Try zooming out or dragging the image to see more areas.' ]
        message_success: [
          'Correct!  The two points are on the same portion of a glossy',
          'surface.' ]
      )
      # BELOW: pages teaching about mirrors.  Mirrors are filtered out by the
      # first task, so we aren't showing them.
      #window.build_content(
        #image_key: '176',
        #x1: 1204, y1: 1030, x2: 1374, y2: 957,
        #message: [
          #'If you see a transparent or reflective object, you should judge the',
          #'closest object, and not the things behind it.  These two points',
          #'have the same surface color.'
        #]
      #)
      #window.build_content(
        #image_key: '104550',
        #x1: 911, y1: 423, x2: 1520, y2: 689,
        #message: [
          #'Similarly for mirrors, judge the surface of the mirror,'
          #'not what you see inside the reflection.  These two points'
          #'are both on the mirror so they have the same surface color.'
        #]
      #)
      #window.build_content(
        #image_key: '104550',
        #x1: 763, y1: 111, x2: 1019, y2: 239,
        #message: [
          #'Finally, since mirrors perfectly reflect light, they have a',
          #'lighter surface color than non-mirror objects.  Therefore, point 1',
          #'is darker than point 2 in this example.'
        #]
      #)
      #window.build_content(
        #image_key: '66',
        #x1: 845, y1: 932, x2: 998, y2: 919,
        #expected_darker: ['E'],
        #expected_confidence: ['1', '2'],
        #message: [
          #'Using the buttons at the top, indicate which point has a darker',
          #'surface color.  Also indicate how confident you are.'
        #]
        #message_darker_error: [
          #'Try again.  We care about the surface, not what is behind it.' ]
        #message_confidence_error: [
          #'You should be able to tell with more accuracy than just guessing.',
          #'Try zooming out or dragging the image to see more areas.' ]
        #message_success: [
          #'Correct!  The two points are on the same portion of a glass',
          #'surface.' ]
      #)
      #window.build_content(
        #image_key: '104550',
        #x1: 1182, y1: 183, x2: 721, y2: 343,
        #expected_darker: ['2'],
        #expected_confidence: ['1', '2'],
        #message: [
          #'Using the buttons at the top, indicate which point has a darker',
          #'surface color.  Also indicate how confident you are.',
        #]
        #message_darker_error: [
          #'Try again.  Remember that mirrors reflect the most light, so they',
          #'have the lightest natural surface color.'
        #]
        #message_confidence_error: [
          #'You should be able to tell with more accuracy than just guessing.',
          #'Try zooming out or dragging the image to see more areas.' ]
        #message_success: [
          #'Correct!  Even though both points look like they are on the',
          #'curtains, one of them is on a mirror.',
        #]
      #)
      #window.build_content(
        #image_key: '104550',
        #x1: 978, y1: 404, x2: 1092, y2: 264,
        #expected_darker: ['E'],
        #expected_confidence: ['1', '2'],
        #message: [
          #'Using the buttons at the top, indicate which point has a darker',
          #'surface color.  Also indicate how confident you are.',
        #]
        #message_darker_error: [
          #'Try again.  Remember that the points are both inside a mirror',
          #'so they have the same natural surface color.'
        #]
        #message_confidence_error: [
          #'You should be able to tell with more accuracy than just guessing.',
          #'Try zooming out or dragging the image to see more areas.' ]
        #message_success: [
          #'Correct!  Always check if the points are inside a mirror.' ]
      #)
      #window.build_content(
        #image_key: '104550',
        #x1: 919, y1: 811, x2: 1046, y2: 748,
        #expected_darker: ['1'],
        #expected_confidence: ['1', '2'],
        #message: [
          #'Using the buttons at the top, indicate which point has a darker',
          #'surface color.  Also indicate how confident you are.',
        #]
        #message_darker_error: [
          #'Try again.  Remember that mirrors reflect the most light, so they.',
          #'have the lightest natural surface color.'
        #]
        #message_confidence_error: [
          #'You should be able to tell with more accuracy than just guessing.',
          #'Try zooming out or dragging the image to see more areas.' ]
        #message_success: [
          #'Correct!  Even though both points look like they are on the tissue',
          #'box, one of them is on a mirror.' ]
      #)
    ]

    $(window).on('resize', debounce(@on_resize))
    $('.response-darker').on('click', @btn_response_darker)
    $('.response-confidence').on('click', @btn_response_confidence)
    $('#btn-next').on('click', @btn_next)
    $('#btn-back').on('click', @btn_back)
    $('#btn-submit').on('click', @btn_submit)

  on_resize: =>
    if not @submit_enabled
      @show_page(@idx)

  btn_submit: =>
    if @submit_enabled
      window.mt_tutorial_complete()

  btn_next: =>
    if not @animating
      if @idx < @tutorial_content.length - 1
        @show_page(@idx + 1)
      else
        @idx += 1
        $('#tut-confidence').hide()
        set_btn_enabled('button.response', false)
        set_btn_enabled('#btn-next', false)
        set_btn_enabled('#btn-back', true)
        @ui.clear_ui()
        $('#mt-done').show()
        @set_submit_enabled(true)

  btn_back: =>
    if not @animating and @idx > 0
      @show_page(@idx - 1)

  btn_response_darker: (event) =>
    if not @animating
      content = @tutorial_content[@idx]
      darker = $(event.target).attr('data-darker')
      if darker in content.expected_darker
        if content.expected_confidence?
          @ui.set_message(content.message)
          set_btn_enabled('button.response-confidence', true)
        else
          @ui.set_message(content.message_success)
          @show_navigation_buttons()
      else
        set_btn_enabled('button.response-confidence', false)
        @ui.set_message(content.message_darker_error)

  btn_response_confidence: (event) =>
    if not @animating
      content = @tutorial_content[@idx]
      confidence = $(event.target).attr('data-confidence')
      if confidence in content.expected_confidence
        @ui.set_message(content.message_success)
        @show_navigation_buttons()
      else
        @ui.set_message(content.message_confidence_error)

  show_page: (idx) ->
    console.log 'show_page', idx
    @idx = idx

    $('#mt-done').hide()
    set_btn_enabled('button.response', false)
    set_btn_enabled('button.controls', false)
    @set_submit_enabled(false)
    @animating = true

    content = @tutorial_content[idx]
    on_end = ( =>
      set_btn_enabled('#btn-back', idx > 0)
      if content.expected_darker?
        @show_response_buttons()
      else
        @show_navigation_buttons()
      @animating = false
    )

    if content.zoom_out
      @ui.update_ui(content, ( =>
        target = @ui.compute_current_zoom()
        target[2] *= 2
        @ui.zoom_to_target(target, on_end)
      ))
    else
      @ui.update_ui(content, on_end)

  show_response_buttons: ->
    set_btn_enabled('button.response-darker', true)
    set_btn_enabled('button.response-confidence', false)
    $('button.response-darker').removeClass('active')

    if @tutorial_content[@idx].expected_confidence?
      $('#tut-confidence').show()
    else
      $('#tut-confidence').hide()

    $('#tut-buttons').show()

  show_navigation_buttons: ->
    $('#tut-buttons').hide()
    set_btn_enabled('#btn-next', @idx < @tutorial_content.length)

  set_submit_enabled: (b) ->
    @submit_enabled = b
    if b
      $('#btn-submit').show()
      set_btn_enabled('#btn-submit', true)
    else
      $('#btn-submit').hide()
