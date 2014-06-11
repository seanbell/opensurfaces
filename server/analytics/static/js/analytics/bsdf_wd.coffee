##
## BSDF statistics page
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
      d.doi = Math.max(0, 1 - (0.001 + (15 - +d.doi) * 0.2 / 15))
      d.contrast = Math.max(0, Math.min(+d.contrast, 1))
      d.color_correct_score = Math.max(-2, Math.min(+d.color_correct_score, 2))
      d.gloss_correct_score = Math.max(-2, Math.min(+d.gloss_correct_score, 2))
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
    doi: 0.02
    contrast: 0.05
    color_correct_score: 0.05
    gloss_correct_score: 0.05

  # project dimensions
  config.dims =
    time_s: config.cf.dimension((d) -> d.time_s)
    doi: config.cf.dimension((d) -> d.doi)
    contrast: config.cf.dimension((d) -> d.contrast)
    color_correct_score: config.cf.dimension((d) -> d.color_correct_score)
    gloss_correct_score: config.cf.dimension((d) -> d.gloss_correct_score)

  config.min =
    doi: 0.8

  # remaining groups and max: default
  add_remaining_groups_and_max(config)

  # the other charts can be done generically
  add_remaining_bar_cf_charts(config)
  finish_cf_charts(config, '#csv-url')
)
