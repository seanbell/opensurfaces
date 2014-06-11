##
## Utilities for pages that compute stats
##

# returns a function that computes units with a given scale
numeric_units = (scale) -> (s, e) ->
  new Array(Math.max(1, Math.floor(Math.abs(s - e) / scale)))

# returns a function that rounds to the nearest scale increment
numeric_round = (scale) -> (d) ->
  Math.round(d / scale) * scale

# default accessor and filter
accessor_identity = (x) -> x
filter_true = (x) -> true

# compute mean and stdev
mean_stdev = (array, accessor=accessor_identity, filter=filter_true) ->
  sum = 0
  count = 0
  for a in array when filter(a)
    sum += accessor(a)
    count += 1

  if count == 0
    return [Number.NaN, Number.NaN]
  else if count == 1
    return [sum, 0]

  mean = sum / count
  var_sum = 0
  for a in array when filter(a)
    x = accessor(a)
    dx = (mean - x)
    var_sum += dx * dx

  return [mean, Math.sqrt(var_sum / (count - 1))]

# computes the width to use for different bootstrap span sizes
span_width = (parent) ->
  if parent.hasClass('span3') then 220
  else if parent.hasClass('span4') then 300
  else if parent.hasClass('span6') then 460
  else if parent.hasClass('span8') then 620
  else if parent.hasClass('span9') then 720
  else if parent.hasClass('span12') then 940
  else
    console.log 'Cannot determine width for:'
    console.log parent
    300

# convert "#RRGGBB" to [h, s, v]
colorhex_to_hsv = (rgb) ->
  r = parseInt(rgb.substring(1, 3), 16) / 255
  g = parseInt(rgb.substring(3, 5), 16) / 255
  b = parseInt(rgb.substring(5, 7), 16) / 255
  # adapted from http://mjijackson.com/2008/02/rgb-to-hsl-and-rgb-to-hsv-color-model-conversion-algorithms-in-javascript
  max = Math.max(r, g, b)
  min = Math.min(r, g, b)
  v = max
  d = max - min
  s = if (max == 0) then 0 else (d / max)
  if max == min
    h = 0 # achromatic
  else
    if max == r
      h = (g - b) / d + (if (g < b) then 6 else 0)
    else if max == g
      h = (b - r) / d + 2
    else # max == b
      h = (r - g) / d + 4
    h /= 6
  return [h, s, v]

##
## Helpers for crossfilter+dc+d3 charts
##

# setup crossfilter and return a config object
init_cf_config = (data) ->
  cf = crossfilter(data)
  all = cf.groupAll()
  dc.dataCount('#data-count').dimension(cf).group(all)

  cf: cf
  all: all
  data: data
  dims: {}
  groups: {}
  max: {}
  min: {}
  scales: {}
  charts: {}


# clip data to its max
clip_data_to_max = (data, max) ->
  data.forEach((d) ->
    for key of max
      d[key] = Math.min(d[key], max[key])
  )


# fills in a default for unspecified max and group attributes
add_remaining_groups_and_max = (config) ->
  for key of config.dims when not config.groups[key]?
    if config.scales[key]?
      # group by bins of size scale[key], rather than by integer (the default)
      config.groups[key] = config.dims[key].group(numeric_round(config.scales[key]))
    else
      # group by default
      config.groups[key] = config.dims[key].group()

  # max is simply largest value (no clipping)
  for key of config.dims when not config.max[key]?
    config.max[key] = d3.max(config.data, (d) -> d[key])

  for key of config.dims when not config.min[key]?
    config.min[key] = d3.min(config.data, (d) -> d[key])
    if min > 0
      min = 0


# adds any un-added charts as a bar chart
add_remaining_bar_cf_charts = (config) ->
  for key of config.dims when not config.charts[key]?
    selector = '#' + key.replace(/_/g, '-') + '-chart'
    $selector = $(selector)
    if $selector.length == 0 then continue
    width = span_width($selector.parent())
    console.log "Bar chart for #{key}: selector #{selector}, width #{width}"

    config.charts[key] = dc.barChart(selector)
      .width(width)
      .height(185)
      .margins({top: 10, right: 20, bottom: 20, left: 40})
      .dimension(config.dims[key])
      .group(config.groups[key])
      .elasticY(true)
      .yAxisPadding(0)
      .x(d3.scale.linear().domain([config.min[key], config.max[key] + config.scales[key]]))
      .xUnits(numeric_units(config.scales[key]))
      .round(numeric_round(config.scales[key]))
      .gap(1)


create_full_data_colors = (data) ->
  category_colors = d3.scale.category20()
  (category_colors(i) for d,i in data)


# performs the last step of setting up crossfilter and dc
finish_cf_charts = (config, parent) ->
  # reset buttons
  for key of config.charts
    $('#' + key.replace(/_/g, '-') + '-reset').on('click', do (key) -> ->
      config.charts[key].filterAll()
      dc.redrawAll()
    )

  # reset events
  $('#reset-all').on('click', ->
    dc.filterAll()
    dc.renderAll()
  )

  # hide loading bar and show page
  $('#loading').hide()
  $(parent).removeClass('hidden')
  dc.renderAll()

  console.log 'charts finished loading'
