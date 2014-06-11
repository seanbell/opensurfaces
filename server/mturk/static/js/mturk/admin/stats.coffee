$( ->
  # fetch the csv
  csv_url = $('#stats-csv').attr('data-url')
  console.log "fetching csv: #{csv_url}"
  d3.csv(csv_url, (data) ->
    if not data
      console.log "error fetching #{csv_url}"
      return

    # format the data
    data.forEach((d) ->
      d.time_s = Math.max(0, Math.min(+d.time_ms / 1000.0, 500))
      d.time_load_ms = Math.max(0, Math.min(+d.time_load_ms, 100000))
      if d.time_load_ms <= 0
        d.time_load_ms = -2000
      d.wage = Math.max(0, Math.min(+d.wage, 20))
    )

    # filter to the particular experiment
    if window.category_slug != 'all'
      data = data.filter((d) -> d.experiment_slug == window.category_slug)

    # initialize with clipped data
    config = init_cf_config(data)

    # dimension bin sizes
    config.scales =
      time_s: 5
      time_load_ms: 500
      wage: 0.25

    # project dimensions
    config.dims =
      time_s: config.cf.dimension((d) -> d.time_s)
      time_load_ms: config.cf.dimension((d) -> d.time_load_ms)
      wage: config.cf.dimension((d) -> d.wage)

    # remaining groups and max: default
    add_remaining_groups_and_max(config)

    # the other charts can be done generically
    add_remaining_bar_cf_charts(config)
    finish_cf_charts(config, '#stats-csv')
  )
)
