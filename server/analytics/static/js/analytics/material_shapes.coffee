##
## shapes statistics page
##

# helper to get all material shapes data and parse it
helper = (callback) -> $( ->
  csv_url = $('#csv-url').attr('data-url')
  console.log "fetching #{csv_url}"

  d3.csv(csv_url, (data) ->
    if not data
      console.log "error fetching #{csv_url}"
      return

    # remove bogus entries
    data = data.filter((d) -> +d.num_vertices >= 3)

    # parse data
    data.forEach((d) ->
      d.time_s = Math.max(0, Math.min(+d.time_ms / 1000.0, 120))
      d.num_vertices = Math.max(0, Math.min(+d.num_vertices, 120))
      d.planar_score = Math.max(-2, Math.min(+d.planar_score, 2))
      #d.added = d3.time.hour(new Date(d.added))
    )

    callback(data)
  )
)


helper( (data) ->

  # initialize with clipped data
  config = init_cf_config(data)

  # dimension bin sizes
  config.scales =
    time_s: 1
    num_vertices: 1
    planar_score: 0.05

  # project dimensions
  config.dims =
    time_s: config.cf.dimension((d) -> d.time_s)
    num_vertices: config.cf.dimension((d) -> d.num_vertices)
    planar_score: config.cf.dimension((d) -> d.planar_score)
    #added: config.cf.dimension((d) -> d.added)

  # remaining groups and max: default
  add_remaining_groups_and_max(config)

  #config.charts =
    #added: dc.lineChart('#added-chart')
      #.width(span_width($('#added-chart').parent()))
      #.height(185)
      #.margins({top: 10, right: 20, bottom: 20, left: 30})
      #.dimension(config.dims.added)
      #.group(config.groups.added)
      #.elasticY(true)
      #.yAxisPadding(10)
      #.x(d3.time.scale().domain(d3.extent(data, (d) -> d.added)).nice(d3.time.day))
      #.xUnits(d3.time.hours)
      #.renderArea(true)

  # the other charts can be done generically
  add_remaining_bar_cf_charts(config)
  finish_cf_charts(config, '#csv-url')
)
