class IntrinsicClassifyUI extends SvgPhotoZoomUI
  constructor: (args) ->
    super(
      container_id: "mt-container"
      compute_ui_dims: ->
        width = $('#mt-container').width()
        height = $(window).height() - $('#mt-top-nohover').height()
        return [width, height]
    )

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

  data_from_content: (content) ->
    data = []
    for d in content.points
      if d.tut_error
        clz = 'tut-error'
        scale = "1.5,1.5"
      else
        clz = (if d.opaque then 'opaque' else 'not-opaque')
        scale = (if d.opaque then '0.5,0.5' else '0.75,0.75')
      data.push([
        d.x * @photo_size.width,
        d.y * @photo_size.height,
        clz,
        if d.opaque then 0 else 45,
        scale,
        d.id,
      ])
    data.sort((a, b) ->
      if a[0] == b[0]
        a[1] - b[1]
      else
        a[0] - b[0]
    )
    return data

  update_ui: (content, on_end=null) ->
    @init_svg()
    @set_photo(content.photo)

    # reset zoom on image change
    if not @photo_url? or content.photo.url != @photo_url
      @reset_zoom()
    @photo_url = content.photo.url

    data = @data_from_content(content)
    data_join = @svg.selectAll('.data-point')
      .data(data, (d) -> d[5])

    ## update
    data_join
      .attr('class', (d) -> 'data-point ' + d[2])
      .transition().duration(250)
        .attr('transform',
          (d) -> "translate(#{d[0]},#{d[1]}) rotate(#{d[3]}) scale(#{d[4]})")
        .style('opacity', 1)

    # enter
    g = data_join.enter().append('g')
      .attr('class', (d) -> 'data-point ' + d[2])
      .attr('transform', (d) -> "translate(#{d[0]},#{d[1]}) scale(5, 5)")
      .style('opacity', 1e-6)

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
      .attr('class', 'outer-point-circle')
      .attr('r', @r1)

    g.append('circle')
      .attr('class', 'inner-point-circle')
      .attr('r', @r1 - 2)

    # enter animation
    g.transition()
      .delay((d, i) -> i * 50)
      .duration(1000)
        .attr('transform',
          (d) -> "translate(#{d[0]},#{d[1]}) rotate(#{d[3]}) scale(#{d[4]})")
        .style('opacity', 1)

    # exit
    data_join.exit()
      .attr('transform',
        (d) -> "translate(#{d[0]},#{d[1]}) rotate(#{d[3]}) scale(#{d[4]})")
      .style('opacity', 1)
      .transition()
        .duration(250)
        .attr('transform', (d) -> "translate(#{d[0]},#{d[1]}) scale(0)")
        .style('opacity', 1e-6)
        .remove()

    # message
    @set_message(content.message)

    # callback
    on_end?()

  get_point_from_click: (content, event) ->
    container_pos = $('#mt-container').position()
    global_x = event.pageX - container_pos.left
    global_y = event.pageY - container_pos.top
    [local_x, local_y] = @compute_local_coords(global_x, global_y)

    r = @r1
    dmin = r * r
    closest = null
    for p in content.points
      dx = p.x * @photo_size.width  - local_x
      dy = p.y * @photo_size.height - local_y
      d = dx * dx + dy * dy
      if d < dmin
        dmin = d
        closest = p
    return closest
