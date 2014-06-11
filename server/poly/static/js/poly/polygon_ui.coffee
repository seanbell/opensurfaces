# UI for one polygon
class PolygonUI
  constructor: (@id, @poly, @stage) ->
    # @stage is an instance of StageUI
    @line = null
    @fill = null
    @text = null
    @hover_line = null
    @hover_fill = null
    @anchors = null
    @stroke_scale = 1.0 / @stage.get_zoom_factor()

  # update stroke scale
  update_zoom: (ui, inv_zoom_factor, redraw=true) ->
    @stroke_scale = inv_zoom_factor
    @update(ui, redraw)

  # update UI elements
  update: (ui, redraw=true) ->
    if @poly.open
      @remove_fill()
      @remove_text()
      @add_line()
      p = @stage.mouse_pos()
      if p? and not @poly.empty()
        @add_hover(p)
      else
        @remove_hover()
    else
      @remove_hover()
      @remove_line()
      @add_fill(ui)
      @add_text()
    if redraw
      @stage.draw()

  # remove UI elements
  remove_line: -> @stage.remove(@line); @line = null
  remove_fill: -> @stage.remove(@fill); @fill = null
  remove_text: -> @stage.remove(@text); @text = null
  remove_hover: ->
    @stage.remove(@hover_fill); @hover_fill = null
    @stage.remove(@hover_line); @hover_line = null
  remove_anchors: -> if @anchors?
    if @anchors.length < 8
      for a in @anchors
        @stage.remove(a, 0.4)
    else
      for a in @anchors
        @stage.remove(a, 0)
    @anchors = null
    @stage.draw()
  remove_all: ->
    @remove_line()
    @remove_fill()
    @remove_text()
    @remove_hover()
    @remove_anchors()

  # add polygon fill
  add_fill: (ui)->
    if @fill?
      @fill.setPoints(@poly.points)
      @fill.setStrokeWidth(2 * @stroke_scale)
    else
      @fill = new Kinetic.Polygon(
        points: @poly.points,
        fill: POLYGON_COLORS[@id % POLYGON_COLORS.length],
        stroke: '#007', strokeWidth: 2 * @stroke_scale,
        lineJoin: 'round')
      @fill.on('click', =>
        if not ui.s.panning
          ui.select_poly(@id)
      )
      @stage.add(@fill, 0.4)

  # add text label
  add_text: ->
    cen = @poly.labelpos()
    label = String(@id + 1)
    pos =
      x: cen.x - 5 * label.length * @stroke_scale
      y: cen.y - 5 * @stroke_scale
    if @text?
      @text.setPosition(pos)
      @text.setText(label)
      @text.setFontSize(10 * @stroke_scale)
    else
      @text = new Kinetic.Text(
        text: label, fill: '#000',
        x: pos.x, y: pos.y, align: 'left',
        fontSize: 10 * @stroke_scale,
        fontFamily: 'Verdana', fontStyle: 'bold')
      @stage.add(@text, 1.0)

  add_line: ->
    if @line?
      @line.setPoints(@poly.points)
      @line.setStrokeWidth(3 * @stroke_scale)
    else
      @line = new Kinetic.Line(
        points: @poly.points, opacity: 0, stroke: "#00F",
        strokeWidth: 3 * @stroke_scale, lineJoin: "round")
      @stage.add(@line, 0.5)

  add_hover: (p) ->
    @add_hover_fill(p)
    @add_hover_line(p)

  add_hover_fill: (p) ->
    hover_points = @poly.points.concat([clone_pt p])
    if @hover_fill?
      @hover_fill.setPoints(hover_points)
    else
      @hover_fill = new Kinetic.Polygon(
        points: hover_points, opacity: 0, fill: "#00F")
      @stage.add(@hover_fill, 0.15)

  add_hover_line: (p) ->
    hover_points = [clone_pt(p), @poly.points[@poly.num_points() - 1]]
    if @hover_line?
      @hover_line.setPoints(hover_points)
      @hover_line.setStrokeWidth(3 * @stroke_scale)
    else
      @hover_line = new Kinetic.Line(
        points: hover_points, opacity: 0, stroke: "#00F",
        strokeWidth: 3 * @stroke_scale, lineCap: "round")
      @stage.add(@hover_line, 0.5)

    if @poly.can_push_point(p)
      @hover_line.setStroke("#00F")
      @hover_line.setStrokeWidth(3 * @stroke_scale)
    else
      @hover_line.setStroke("#F00")
      @hover_line.setStrokeWidth(10 * @stroke_scale)

  add_anchors: (ui) ->
    if ui.s.draw_mode then return
    if @anchors?
      if @anchors.length == @poly.points.length
        for p, i in @poly.points
          @anchors[i].setPosition(p.x, p.y)
          @anchors[i].setStrokeWidth(2 * @stroke_scale)
          @anchors[i].setRadius(10 * @stroke_scale)
        return
      @remove_anchors()

    @anchors = []
    for p, i in @poly.points
      v = new Kinetic.Circle(
        x: p.x, y: p.y,
        radius: 10 * @stroke_scale,
        strokeWidth: 2 * @stroke_scale,
        stroke: "#666", fill: "#ddd",
        opacity: 0, draggable: true)

      v.on('mouseover', do (v) => =>
        if v.removing != true
          $('canvas').css('cursor', 'pointer')
          v.setStrokeWidth(4 * @stroke_scale)
          @stage.draw()
      )
      v.on('mouseout',  do (v) => =>
        if v.removing != true
          $('canvas').css('cursor', 'default')
          v.setStrokeWidth(2 * @stroke_scale)
          @stage.draw()
      )
      v.on('mousedown', do (i) => =>
        if v.removing != true
          ui.start_drag_point(i)
      )

      v.on('dragmove', do (i) => =>
        ui.progress_drag_point(i, @anchors[i].getPosition())
        if @fill
          if ui.drag_valid(i)
            @fill.setStrokeWidth(2 * @stroke_scale)
            @fill.setStroke("#007")
          else
            @fill.setStrokeWidth(10 * @stroke_scale)
            @fill.setStroke("#F00")
      )

      v.on('dragend', do (i) => =>
        if ui.drag_valid(i)
          ui.finish_drag_point(i, @anchors[i].getPosition())
        else
          ps = ui.revert_drag_point(i)
          if ps? then @anchors[i].setPosition(ps.x, ps.y)
        @fill.setStrokeWidth(2 * @stroke_scale)
        @fill.setStroke("#007")
        @update(ui)
      )

      if @poly.points.length < 8
        @stage.add(v, 0.5, 0.4)
      else
        @stage.add(v, 0.5, 0)
      @anchors.push(v)
