# Main control logic for the UI.  Actions in this class delegate through
# undo/redo and check whether something is feasible.
class ControllerUI
  constructor: (args) ->
    @s = new ControllerState(@, args)

    # disable right click
    $(document).on('contextmenu', (e) =>
      @click(e)
      false
    )

    # capture all clicks and disable text selection
    $(document)
      .on('click', @click)
      .on('mousedown', @mousedown)
      .on('mouseup', @mouseup)
      .on('mousemove', @mousemove)
      .on('selectstart', -> false)

    # init buttons
    $(@s.btn_draw).on('click', =>
      if not @s.draw_mode then @toggle_mode())
    $(@s.btn_edit).on('click', =>
      if @s.draw_mode then @toggle_mode())
    $(@s.btn_close).on('click', =>
      if not @s.loading then @close_poly())
    $(@s.btn_delete).on('click', =>
      if not @s.loading then @delete_sel_poly())
    $(@s.btn_zoom_reset).on('click', =>
      if not @s.loading then @zoom_reset())

    # log instruction viewing
    $('#modal-instructions').on('show', =>
      @s.log.action(name: "ShowInstructions")
    )
    $('#modal-instructions').on('hide', =>
      @s.log.action(name: "HideInstructions")
    )

    # keep track of modal state
    # (since we want to allow scrolling)
    $('.modal').on('show', =>
      @s.modal_count += 1
      true
    )
    $('.modal').on('hide', =>
      @s.modal_count -= 1
      true
    )

    # listen for scrolling
    $(window).on('mousewheel DOMMouseScroll', @wheel)

    # listen for translation
    $(window)
      .on('keydown', @keydown)
      .on('keyup', @keyup)
      .on('blur', @blur)

    # keep track of invalid close attempts to show a
    # popup explaining the problem
    @num_failed_closes = 0

    # init photo
    if args.photo_url? then @set_photo(args.photo_url)

  get_submit_data: =>
    @s.get_submit_data()

  set_photo: (photo_url) =>
    @s.disable_buttons()
    @s.loading = true
    @s.stage_ui.set_photo(photo_url, @, =>
      console.log "loaded photo_url: #{photo_url}"
      @s.loading = false
      @s.update_buttons()
    )

  keydown: (e) =>
    if @s.modal_count > 0 then return true
    switch e.keyCode
      when 37 # left
        @s.translate_delta(-20, 0)
        false
      when 38 # up
        @s.translate_delta(0, -20)
        false
      when 39 # right
        @s.translate_delta(20, 0)
        false
      when 40 # down
        @s.translate_delta(0, 20)
        false
      when 32 # space
        @s.panning = true
        @s.update_cursor()
        false
      when 68 # D
        if not @s.draw_mode then @toggle_mode()
        false
      when 65 # A
        if @s.draw_mode then @toggle_mode()
        false
      when 46,8 # delete,backspace
        if @s.draw_mode
          @remove_open_poly()
        else
          @delete_sel_poly()
        false
      when 27 # esc
        if @s.draw_mode
          @s.zoom_reset()
        else
          @unselect_poly()
        false
      else
        true

  keyup: (e) =>
    @s.panning = false
    if @s.modal_count > 0 then return true
    @s.update_cursor()
    return true

  blur: (e) =>
    @s.panning = false
    @s.mousedown = false
    if @s.modal_count > 0 then return true
    @s.update_cursor()
    return true

  wheel: (e) =>
    if @s.modal_count > 0 then return true
    oe = e.originalEvent
    if oe.wheelDelta?
      @s.zoom_delta(oe.wheelDelta)
    else
      @s.zoom_delta(oe.detail * -60)
    window.scrollTo(0, 0)
    stop_event(e)

  zoom_reset: (e) =>
    @s.zoom_reset()

  click: (e) =>
    if @s.panning then return
    p = @s.mouse_pos()
    if not p? then return
    if not @s.loading and @s.draw_mode
      if e.button > 1
        @close_poly()
      else
        if @s.open_poly?
          ue = new UEPushPoint(p)
          if @s.open_poly.poly.can_push_point(p)
            @s.undoredo.run(ue)
          else
            @s.log.attempted(ue.entry())
        else
          @s.undoredo.run(new UECreatePolygon(
            @s.stage_ui.mouse_pos()))
        @s.stage_ui.translate_mouse_click()

  mousedown: (e) =>
    if @s.modal_count > 0 then return true
    @s.mousedown = true
    @s.mousepos = {x: e.pageX, y: e.pageY}
    @s.update_cursor()
    return not @s.panning

  mouseup: (e) =>
    @s.mousedown = false
    if @s.modal_count > 0 then return true
    @s.update_cursor()
    return not @s.panning

  mousemove: (e) =>
    if @s.modal_count > 0 then return true
    if @s.mousedown and @s.panning
      scale = 1.0 / @s.stage_ui.get_zoom_factor()
      @s.stage_ui.translate_delta(
        scale * (@s.mousepos.x - e.pageX),
        scale * (@s.mousepos.y - e.pageY),
        false)
      @s.mousepos = {x: e.pageX, y: e.pageY}
    return true

  update: =>
    @s.open_poly?.update(@)
    @s.sel_poly?.update(@)

  close_poly: => if not @s.loading
    ue = new UEClosePolygon()
    if @s.can_close()
      @s.undoredo.run(ue)
    else
      @s.log.attempted(ue.entry())
      if @s.open_poly?
        pts = @s.open_poly.poly.points
        if pts.length >= 2
          @s.stage_ui.error_line(pts[0], pts[pts.length - 1])
          @num_failed_closes += 1

      if @num_failed_closes >= 3
        @num_failed_closes = 0
        $('#poly-modal-intersect').modal('show')

  select_poly: (id) =>
    @s.undoredo.run(new UESelectPolygon(id))

  unselect_poly: (id) =>
    @s.undoredo.run(new UEUnselectPolygon())

  remove_open_poly: (id) =>
    @s.undoredo.run(new UERemoveOpenPoly())

  delete_sel_poly: =>
    ue = new UEDeletePolygon()
    if @s.can_delete_sel()
      @s.undoredo.run(ue)
    else
      @s.log.attempted(ue.entry())

  start_drag_point: (i) =>
    p = @s.sel_poly.poly.get_pt(i)
    @s.drag_valid_point = clone_pt(p)
    @s.drag_start_point = clone_pt(p)

  revert_drag_point: (i) =>
    @s.undoredo.run(new UEDragVertex(i,
      @s.drag_start_point, @s.drag_valid_point))

  progress_drag_point: (i, p) =>
    @s.sel_poly.poly.set_point(i, p)
    if @drag_valid(i) then @s.drag_valid_point = clone_pt(p)

  finish_drag_point: (i, p) =>
    @s.undoredo.run(new UEDragVertex(i, @s.drag_start_point, p))
    @s.drag_valid_point = null
    @s.drag_start_point = null

  drag_valid: (i) =>
    not @s.sel_poly.poly.self_intersects_at_index(i)

  toggle_mode: =>
    @s.undoredo.run(new UEToggleMode())

  on_photo_loaded: =>
    @s.update_buttons()
    @s.stage_ui.init_events()
