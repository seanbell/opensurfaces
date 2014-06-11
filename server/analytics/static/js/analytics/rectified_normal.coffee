##
## rectified normal statistics page
##

# helper to get all BSDF data and parse it
helper = (callback) -> $( ->
  csv_url = $('#csv-url').attr('data-url')
  console.log "fetching #{csv_url}"

  d3.csv(csv_url, (data) ->
    if not data
      console.log "error fetching #{csv_url}"
      return

    # remove bogus entries
    #data = data.filter((d) -> +d.num_vertices >= 3)

    # parse data
    data.forEach((d) ->
      d.time_s = Math.max(0, Math.min(+d.time_ms / 1000.0, 120))
      d.correct_score = Math.max(-2, Math.min(+d.correct_score, 2))
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
    correct_score: 0.05

  # project dimensions
  config.dims =
    time_s: config.cf.dimension((d) -> d.time_s)
    correct_score: config.cf.dimension((d) -> d.correct_score)

  # remaining groups and max: default
  add_remaining_groups_and_max(config)

  # the other charts can be done generically
  add_remaining_bar_cf_charts(config)
  finish_cf_charts(config, '#csv-url')
)
