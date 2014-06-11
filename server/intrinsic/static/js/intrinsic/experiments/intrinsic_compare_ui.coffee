class IntrinsicCompareUI extends SvgPhotoZoomUI
  constructor: ->
    super(
      container_id: "mt-container"
      compute_ui_dims: ->
        width = $('#mt-container').width()
        height = $(window).height() - $('#mt-top-nohover').height()
        return [width, height]
    )

    @extra_margin = 20
    @r1 = 20
    @r2 = 3.5

  build_static_svg: ->
    for f in [['tri0', '#000'], ['tri1', '#fff']]
      @svg
        .append("marker")
          .attr("id", f[0])
          .attr("viewBox", "0 0 10 10")
          .attr("refX", 0)
          .attr("refY", 5)
          .attr("markerWidth", 1.5)
          .attr("markerHeight", 1.0)
          .attr("orient", "auto")
        .append("path")
          .attr("d", "M 0 0 L 10 5 L 0 10 z")
          .style('fill', f[1])

  highlight: (content) ->
    data = @data_from_content(content)
    @zoom_behavior.scale(1)
    @zoom_behavior.translate([0, 0])
    @zoom_to_points(data, ( =>
      @svg.selectAll('.data-point')
        .data(data, (d) -> d)
        .transition()
          .duration(250)
          .style('opacity', 1)
          .attr('transform',
            (d) -> "translate(#{d[0]},#{d[1]}) scale(1.5)")
        .transition()
          .duration(250)
          .attr('transform',
            (d) -> "translate(#{d[0]},#{d[1]})")
        .transition().duration(150).style('opacity', 1e-6)
        .transition().duration(150).style('opacity', 1)
        .transition().duration(150).style('opacity', 1e-6)
        .transition().duration(150).style('opacity', 1)
    ))

  data_from_content: (content) ->
    data = []
    for d in content.points
      data.push([
        d.x_orig * @photo_size.width,
        d.y_orig * @photo_size.height,
        d.color,
        d.label,
      ])
    return data

  update_ui: (content, on_end=null) ->
    @init_svg()
    @set_photo(content.photo)

    # reset zoom on image change
    if not @photo_url? or content.photo.url != @photo_url
      photo_changed = true
      @reset_zoom()
    else
      photo_changed = false
    @photo_url = content.photo.url

    data = @data_from_content(content)
    data_join = @svg.selectAll('.data-point')
      .data(data, (d) -> d)

    # make circles smaller if they are overlapping
    if data.length == 2
      sq = (x) -> x * x
      point_dist_sq = sq(data[0][0] - data[1][0]) + sq(data[0][1] - data[1][1])
      point_dist = Math.sqrt(point_dist_sq) / 3
      scale = Math.min(point_dist / @r1, 1)
    else
      scale = 1

    # enter
    g = data_join.enter()
      .append('g')
        .attr('class', 'data-point')

    for f in [0, 1]
      g.append('line').attr('class', "point-line#{f}")
        .attr('marker-end', "url(#tri#{f})")
        .attr('x1', -@r1).attr('y1', 0).attr('x2', -@r2).attr('y2', 0)
      g.append('line').attr('class', "point-line#{f}")
        .attr('marker-end', "url(#tri#{f})")
        .attr('x1', @r1).attr('y1', 0).attr('x2', @r2).attr('y2', 0)
      g.append('line').attr('class', "point-line#{f}")
        .attr('marker-end', "url(#tri#{f})")
        .attr('x1', 0).attr('y1', -@r1).attr('x2', 0).attr('y2', -@r2)
      g.append('line').attr('class', "point-line#{f}")
        .attr('marker-end', "url(#tri#{f})")
        .attr('x1', 0).attr('y1', @r1).attr('x2', 0).attr('y2', @r2)

    g.append('circle')
      .attr('class', 'point-circle')
      .attr('r', @r1)
      .style('stroke', (d) -> d[2])

    g.append('circle')
      .attr('class', 'point-circle')
      .attr('r', @r1 - 1)
      .style('stroke', '#fff')

    g.append('circle')
      .attr('class', 'point-label-bg')
      .attr('transform', "translate(#{-@r1},#{-@r1})")
      .attr('cx', 0)
      .attr('cy', -4)
      .attr('r', 8)
      .style('fill', (d) -> d[2])

    g.append('text')
      .attr('class', 'point-label')
      .attr('transform', "translate(#{-@r1},#{-@r1})")
      .text((d) -> d[3])

    # enter animation
    g
        .attr('transform', (d) -> "translate(#{d[0]},#{d[1]}) scale(0,0)")
        .style('opacity', 1e-6)
      .transition()
        .duration(500)
        .attr('transform', (d) -> "translate(#{d[0]},#{d[1]}) scale(#{scale},#{scale})")
        .style('opacity', 1)

    # exit
    data_join.exit()
      .attr('transform', (d) -> "translate(#{d[0]},#{d[1]}) scale(#{scale},#{scale})")
      .style('opacity', 1)
      .transition()
        .duration(500)
        .attr('transform', (d) -> "translate(#{d[0]},#{d[1]}) scale(0,0)")
        .style('opacity', 1e-6)
        .remove()

    # message
    @set_message(content.message)

    do_zoom = =>
      @zoom_to_points(data, ( =>
        @svg.selectAll('.data-point')
          .data(data, (d) -> d)
          .transition()
            .duration(250)
            .style('opacity', 1)
            .attr('transform',
              (d) -> "translate(#{d[0]},#{d[1]}) scale(#{1.25*scale},#{1.25*scale})")
          .transition()
            .duration(250)
            .attr('transform',
              (d) -> "translate(#{d[0]},#{d[1]}) scale(#{scale},#{scale})")

        on_end?()
      ))

    if photo_changed and content.zoom_delay?
      window.setTimeout(do_zoom, content.zoom_delay)
    else
      do_zoom()

  # zoom such that the points are well centered
  zoom_to_points: (data, on_end=null) =>
    @zoom_to_target(@compute_target_zoom(data), on_end)

  # compute the center and width of the zoom box
  compute_target_zoom: (data) ->
    midpoint =
      x: (data[0][0] + data[1][0]) / 2
      y: (data[0][1] + data[1][1]) / 2

    pbox =
      width: @extra_margin + 2 * @r1 + Math.min(
        @width, 1.5 * Math.abs(data[0][0] - data[1][0]))
      height: @extra_margin + 2 * @r1 + Math.min(
        @height, 1.5 * Math.abs(data[0][1] - data[1][1]))
    width = pbox.width
    if pbox.height * @width / width > @height
      width = @width / (@height / pbox.height)
    if @width / width > @max_auto_zoom
      width = @width / @max_auto_zoom

    return [midpoint.x, midpoint.y, width]
