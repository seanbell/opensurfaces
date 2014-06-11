$( ->
  template_args.width = $('#mt-container').width() - 4
  template_args.height = $(window).height() - $('#mt-top-nohover').height() - 16
  template_args.container_id = 'mt-container'
  $('#poly-container').width(template_args.width).height(template_args.height)
  window.controller_ui = new ControllerUI(template_args)
)

btn_submit = ->
  window.mt_submit(window.controller_ui.get_submit_data)

# wait for everything to load before allowing submit
$(window).on('load', ->
  $('#btn-submit').on('click', btn_submit)
)
