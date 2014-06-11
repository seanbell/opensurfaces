$ ->

  $("#nav-logout").on("click", ->
    $.ajax("/account/logout/",
      type: "POST"
      success: ->
        window.location = "/"
      error: ->
        window.hide_modal_loading()
        window.show_modal_error("Could not contact server.")
    )

    $(".dropdown-menu").hide()
    window.show_modal_loading("Logging out...", 200)
    false
  )

  setup_login_form(
    selector: "#nav-login"
    url: "/account/login-ajax/"
    url_fallback: "/account/login/"
    label: "Log in"
    yes_text: "Log in"
  )

  setup_login_form(
    selector: "#nav-signup"
    url: "/account/signup-ajax/"
    url_fallback: "/account/signup/"
    label: "Create a new account"
    yes_text: "Sign up"
  )

# called twice: once for login, once for signup
setup_login_form = (config) ->
  login_yes = ->
    loaded = false
    setTimeout (->
      if not loaded then $("#modal-form-body").find(".progress").fadeIn()
    ), 200
    $.ajax(config.url,
      type: "POST"
      data: $("#modal-form-body > form").serialize()
      success: (data) ->
        loaded = true
        if data.slice(0, 5) is "<form"
          show_login data
          $("#modal-form-body").find(".progress").hide()
          $("#modal-form-body").find("input").filter(->
            $(this).val() is ""
          ).first().focus()
        else
          location.reload(true)
      error: (data) ->
        window.hide_modal_form()
        window.show_modal_error("Could not contact server.")
    )
    false


  show_login = (data) ->
    window.show_modal_form(
      yes_text: config.yes_text
      no_text: "Cancel"
      label: config.label
      body: data
      yes: login_yes
      before_show: ->
        $("#modal-form-body > form").on "keypress", (e) ->
          if e.keyCode == 13
            login_yes()
    )


  $(config.selector).on "click", ->
    $.ajax(config.url,
      type: "GET"
      timeout: 1000
      success: (data) ->
        show_login data
      error: ->
        window.location = config.url_fallback
    )
    false
