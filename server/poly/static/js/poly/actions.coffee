# Control encapsulated into UndoableEvent objects
class UEToggleMode extends UndoableEvent
  constructor: ->
    @open_points = null
    @sel_poly_id = null

  run: (ui) ->
    if ui.s.draw_mode
      if ui.s.open_poly?
        @open_points = ui.s.open_poly.poly.clone_points()
    else
      @sel_poly_id = ui.s.sel_poly?.id
    ui.s.toggle_mode()
    ui.s.update_buttons()

  redo: (ui) ->
    ui.s.toggle_mode()
    ui.s.update_buttons()

  undo: (ui) ->
    ui.s.toggle_mode()
    if ui.s.draw_mode
      if @open_points?
        ui.s.create_poly(@open_points)?.update(ui)
    else
      if @sel_poly_id?
        ui.s.select_poly(ui, @sel_poly_id)?.update(ui)

  entry: -> { name: "UEToggleMode" }

class UERemoveOpenPoly extends UndoableEvent
  constructor: ->
    @open_points = null

  run: (ui) ->
    if ui.s.open_poly?
      @open_points = ui.s.open_poly.poly.clone_points()
    ui.s.remove_open_poly()
    ui.s.update_buttons()

  redo: (ui) ->
    ui.s.remove_open_poly()
    ui.s.update_buttons()

  undo: (ui) ->
    if @open_points?
      ui.s.create_poly(@open_points)?.update(ui)

  entry: -> { name: "UERemoveOpenPoly" }

class UEPushPoint extends UndoableEvent
  constructor: (p) -> @p = clone_pt(p)
  run: (ui) -> ui.s.push_point(@p)?.update(ui)
  undo: (ui) -> ui.s.pop_point()?.update(ui)
  entry: -> { name: "UEPushPoint", args: { p: @p } }

class UECreatePolygon extends UndoableEvent
  constructor: (p) -> @p = clone_pt(p)
  run: (ui) -> ui.s.create_poly([@p])?.update(ui)
  undo: (ui) -> ui.s.remove_open_poly()?.update(ui)
  entry: -> { name: "UECreatePolygon", args: { p: @p } }

class UEClosePolygon extends UndoableEvent
  run: (ui) -> ui.s.close_poly()?.update(ui)
  undo: (ui) -> ui.s.unclose_poly()?.update(ui)
  entry: -> { name: "UEClosePolygon" }

class UESelectPolygon extends UndoableEvent
  constructor: (@id) ->
  run: (ui) ->
    @sel_poly_id = ui.s.sel_poly?.id
    ui.s.select_poly(ui, @id)
  undo: (ui) ->
    if @sel_poly_id?
      ui.s.select_poly(ui, @sel_poly_id)
    else
      ui.s.unselect_poly()
  redo: (ui) ->
    ui.s.select_poly(ui, @id)
  entry: -> { name: "UESelectPolygon", args: { id: @id } }

class UEUnselectPolygon extends UndoableEvent
  constructor: () ->
  run: (ui) ->
    @sel_poly_id = ui.s.sel_poly?.id
    ui.s.unselect_poly()
  undo: (ui) ->
    if @sel_poly_id?
      ui.s.select_poly(ui, @sel_poly_id)
  redo: (ui) ->
    ui.s.unselect_poly()
  entry: -> { name: "UEUnselectPolygon" }

class UEDeletePolygon extends UndoableEvent
  run: (ui) ->
    @points = ui.s.sel_poly.poly.clone_points()
    @time_ms = ui.s.sel_poly.time_ms
    @time_active_ms = ui.s.sel_poly.time_active_ms
    @sel_poly_id = ui.s.sel_poly.id
    ui.s.delete_sel_poly()
    for p,i in ui.s.closed_polys
      p.id = i
      p.update(ui)
  undo: (ui) ->
    ui.s.insert_closed_poly(@points, @sel_poly_id,
      @time_ms, @time_active_ms)
    for p,i in ui.s.closed_polys
      p.id = i
      p.update(ui)
    ui.s.select_poly(ui, @sel_poly_id)
  entry: -> { name: "UEDeletePolygon" }

class UEDragVertex extends UndoableEvent
  constructor: (@i, p0, p1) ->
    @p0 = clone_pt(p0)
    @p1 = clone_pt(p1)
  run: (ui) ->
    sp = ui.s.sel_poly
    sp.poly.set_point(@i, @p1)
    sp.anchors[@i].setPosition(@p1.x, @p1.y)
    sp.update(ui)
  undo: (ui) ->
    sp = ui.s.sel_poly
    sp.poly.set_point(@i, @p0)
    sp.anchors[@i].setPosition(@p0.x, @p0.y)
    sp.update(ui)
  entry: -> { name: "UEDragVertex", args: { i: @i, p0: @p0, p1: @p1 } }
