class SvgPhotoZoomUI
  constructor: (args) ->
    @container_id = args.container_id
    @compute_ui_dims = args.compute_ui_dims

    [@width, @height] = @compute_ui_dims()
    @max_zoom = 16
    @max_auto_zoom = 4
    @zoom_duration_factor = 1.25
    @cur_message = null

  clear_ui: ->
    @svg = null
    if @svg_container?
      @svg_container.remove()
      @svg_container = null

  init_svg: ->
    old_width = @width
    old_height = @height
    [@width, @height] = @compute_ui_dims()

    if not @svg? or @width != old_width or @height != old_height
      @clear_ui()
      @build_photo_svg()
      @build_static_svg()

  build_static_svg: ->
    # build rest of fixed UI here in child class

  build_photo_svg: ->
    @zoom_behavior = d3.behavior.zoom()
      .scaleExtent([1, @max_zoom])
      .size([@width, @height])
      .on('zoom', @on_zoom)

    @svg_container = d3.select("##{@container_id}")
      .append("svg")
        .attr("class", 'svg-container')
        .attr("width", @width)
        .attr("height", @height)

    @svg = @svg_container
      .append('g')
        .call(@zoom_behavior)
      .append('g')

    @svg_image = @svg.append('image')

    @cur_message = null
    @svg_message = @svg_container
      .append('g')
        .style('opacity', 1e-6)

    @svg_message.append('rect')
      .attr('class', 'message')
      .attr('x', 0)
      .attr('y', 0)
      .attr('width', @width)
      .attr('height', 115)
      .style('opacity', 0.7)

    @svg_message.append('text')
      .attr('class', 'message')
      .attr('y', 10)

    @svg.append("rect")
      .attr("class", "pointer-overlay")
      .attr("x", -@width)
      .attr("y", -@height)
      .attr("width", @width * 3)
      .attr("height", @height * 3)

  on_zoom: =>
    @svg.attr('transform',
      "translate(#{@zoom_behavior.translate()}),
       scale(#{@zoom_behavior.scale()})")

  set_photo: (photo) ->
    @photo_size = compute_dimensions(photo.obj, @)
    @svg_image
      .attr('xlink:href', photo.url)
      .attr('width', @photo_size.width)
      .attr('height', @photo_size.height)

  get_zoom_scale: ->
    @zoom_behavior.scale()

  remove_message: ->
    @set_message(undefined)

  set_message: (message) =>
    if @cur_message != message
      add_message = =>
        if message?
          text = @svg_message.select('text')
          text.selectAll('tspan').remove()
          for m in message
            text.append('tspan')
              .attr('x', 20)
              .attr('dy', '1.3em')
              .text(m)
          @svg_message
            .transition()
              .duration(250)
              .style('opacity', 1)
              .each('end', => @cur_message = message)
      if @cur_message?
        @cur_message = null
        @svg_message.transition()
          .duration(250)
          .style('opacity', 1e-6)
          .each('end', add_message)
      else
        add_message()

  # smoothly zoom to target
  # target: [center x, center y, width]
  zoom_to_target: (target, on_end=null) =>
    interpolate = d3.interpolateZoom(
      @compute_current_zoom(), target)
    duration = interpolate.duration * @zoom_duration_factor

    transition = d3.transition().duration(duration).tween("zoom", (
      => (time) =>
        iz = interpolate(time)
        scale = @width / iz[2]
        @zoom_behavior.scale(scale)
        @zoom_behavior.translate([
          (@width / 2 - iz[0] * scale),
          (@height / 2 - iz[1] * scale)]
        )
        @on_zoom()
    ))

    if on_end?
      transition.each("end", on_end)

  # snap zoom to target
  # target: [center x, center y, width]
  set_zoom_target: (target) ->
    scale = @width / target[2]
    @zoom_behavior.scale(scale)
    @zoom_behavior.translate([
      (@width / 2 - target[0] * scale),
      (@height / 2 - target[1] * scale)]
    )
    @on_zoom()

  zoom_in: (factor=1.5) ->
    [cx, cy, w] = @compute_current_zoom()
    @set_zoom_target([cx, cy, Math.max(w / factor, @width / @max_zoom)])

  zoom_out: (factor=1.5) ->
    [cx, cy, w] = @compute_current_zoom()
    @set_zoom_target([cx, cy, Math.min(w * factor, @width)])

  reset_zoom: ->
    @zoom_behavior.scale(1)
    @zoom_behavior.translate([0, 0])
    @on_zoom()

  # compute the current center and width of the zoom box
  compute_current_zoom: ->
    cur_s = @zoom_behavior.scale()
    cur_t = @zoom_behavior.translate()
    cur_c = [
      (@width / 2 - cur_t[0]) / cur_s,
      (@height / 2 - cur_t[1]) / cur_s
    ]
    return [cur_c[0], cur_c[1], @width / cur_s]

  # compute the local coordinates of the global svg coordinates x, y
  compute_local_coords: (x, y) ->
    cur_s = @zoom_behavior.scale()
    cur_t = @zoom_behavior.translate()
    return [
      (x - cur_t[0]) / cur_s,
      (y - cur_t[1]) / cur_s
    ]
