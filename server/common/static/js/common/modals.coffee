## LOGIC FOR MODAL DIALOGS

## templates/modal_areyousure.html

window.show_modal_areyousure = (args) ->
  $("#modal-areyousure-label").html(args.label)  if args.label?
  $("#modal-areyousure-message").html(args.message)  if args.message?
  $("#modal-areyousure-yes").text(args.yes_text)  if args.yes_text?
  $("#modal-areyousure-no").text(args.no_text)  if args.no_text?
  $("#modal-areyousure-yes").off("click").on("click", args.yes)  if args.yes?
  $("#modal-areyousure-no").off("click").on("click", args.no)  if args.no?
  args.before_show?()
  $("#modal-areyousure").modal("show")


## templates/modal_error.html

window.show_modal_error = (message, header) ->
  $("#modal-error-label").html(if header? then header else "Error!")
  $("#modal-error-message").html(message)
  $("#modal-error").modal("show")

window.hide_modal_error = ->
  $("#modal-error").modal("hide")


## templates/modal_form.html

window.show_modal_form = (args) ->
  $("#modal-form-label").html(args.label)  if args.label?
  $("#modal-form-body").html(args.body)  if args.body?
  $("#modal-form-yes").text(args.yes_text)  if args.yes_text?
  $("#modal-form-no").text(args.no_text)  if args.no_text?
  $("#modal-form-yes").off("click").on "click", args.yes  if args.yes?
  $("#modal-form-no").off("click").on "click", args.no  if args.no?
  args.before_show?()
  $("#modal-form").off("shown").on("shown", ->
    $("#modal-form-body").find("input").filter(->
      $(this).val() is ""
    ).first().focus()
  )
  $("#modal-form").modal("show")

window.hide_modal_form = ->
  $("#modal-form").modal("hide")


## templates/modal_give_up.html

window.show_modal_give_up = (label_message, prompt_message, submit_message, suggested_reasons) ->
  $("#modal-give-up-text").val("")
  $("#modal-give-up-label").text(label_message)
  $("#modal-give-up-prompt").text(prompt_message)
  $("#modal-give-up-submit").text(submit_message)
  $("#modal-give-up-submit").attr("disabled", "disabled")
  reasons = $("#modal-give-up-suggested-reasons")
  reasons.empty()
  if suggested_reasons?
    for str in suggested_reasons
      r = $("<button class='btn btn-block' type='button'>#{str}</button>")
      r.on("click", ->
        $("#modal-give-up-text").val(str)
        $("#modal-give-up-submit").removeAttr("disabled")
      )
      reasons.append(r)
    reasons.append $("<p style='margin-top:20px;'>Other problem:</p>")
  $("#modal-give-up").modal "show"

window.hide_modal_give_up = ->
  $("#modal-give-up").modal "hide"

$ ->
  $("#modal-give-up-text").on("input propertychange", ->
    text = $("#modal-give-up-text").val()
    if text and text.length > 10
      $("#modal-give-up-submit").removeAttr("disabled")
    else
      $("#modal-give-up-submit").attr("disabled", "disabled")
  )


## templates/modal_loading.html

window.modal_loading_timeout = null

window.show_modal_loading = (message, timeout) ->
  if window.modal_loading_timeout?
    clearTimeout(window.modal_loading_timeout)
    window.modal_loading_timeout = null

  message = "Loading..."  unless message?
  timeout = 1000  unless timeout?

  window.modal_loading_timeout = setTimeout(( ->
    window.modal_loading_timeout = null
    $("#modal-loading-label").text(message)
    $("#modal-loading").modal(
      backdrop: "static"
      keyboard: false
    ).modal("show")
  ), timeout)

window.hide_modal_loading = (on_hide) ->
  $modal = $("#modal-loading")
  if window.modal_loading_timeout?
    clearTimeout(window.modal_loading_timeout)
    window.modal_loading_timeout = null
    on_hide?()
  else
    if on_hide?
      $modal.off("hidden").on("hidden", ( ->
        $modal.off("hidden")
        setTimeout(on_hide, 100)
      ))
    $modal.modal("hide")


## templates/modal_feedback.html

window.show_modal_feedback = (label_message, prompt_message, on_submit) ->
  $("#modal-feedback-label").empty()
  $("#modal-feedback-prompt").empty()

  if label_message?
    $("#modal-feedback-label").html(label_message)
  if prompt_message?
    $("#modal-feedback-prompt").html(prompt_message)
  if on_submit?
    $("#modal-feedback-submit").off("click").on("click", on_submit)

  $("#modal-feedback").modal("show")

window.get_modal_feedback = ->
  feedback = {}
  $('.modal-feedback-label').each( ->
    field = $(@).attr('data-field')
    value = $.trim($("#modal-feedback-#{field}").val())
    if value
      feedback[field] = value
  )
  return feedback
