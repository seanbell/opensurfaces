window.charts =
  count_freqs: (values) ->
    counts = {}
    values.map((d) -> if counts[d]? then counts[d] += 1 else counts[d] = 1)
    ({name: key, frequency: counts[key]} for key of counts)

  category_histogram: (args) ->
    margin = (if args.margin? then args.margin else {top: 10, right: 10, bottom: 20, left: 10})
    width = (if args.width? then args.width else 210) - margin.left - margin.right
    height = (if args.height? then args.height else 210) - margin.top - margin.bottom
    xpadding = (if args.xpadding? then args.xpadding else 1)

    formatCount = d3.format(",.0f")

    data = charts.count_freqs(args.values)

    x = d3.scale.ordinal()
      .domain(data.map((d) -> d.name ))
      .rangeRoundBands([0, width], 0.1)

    y = d3.scale.linear()
      .domain([0, d3.max(data, (d) -> d.frequency)])
      .range([height, 0])

    xAxis = d3.svg.axis()
      .scale(x)
      .orient("bottom")

    svg = d3.select(args.selector).append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")")

    svg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis)

    bar = svg.selectAll(".bar")
      .data(data)
      .enter().append("g")
      .attr("class", "bar")
      .attr("transform", (d) -> "translate(#{x(d.frequency)}, 0)")

    bar.append("rect")
      .attr('x', xpadding)
      .attr('width', x.rangeBand() - xpadding)
      .attr('y', height)
      .attr('height', 0)
      .transition()
        .delay((d, i) -> i * 200 / data.length)
        .attr('y', (d) -> y(d.frequency))
        .attr('height', (d) -> height - y(d.frequency))

    bar.append("text")
      .attr("dy", ".75em")
      .attr("y", (d) -> y(d.frequency) + 6)
      .attr("x", x.rangeBand() / 2)
      .attr("text-anchor", "middle")
      .text((d) -> formatCount(d.frequency))

  histogram: (args) ->
    margin = (if args.margin? then args.margin else {top: 10, right: 10, bottom: 25, left: 25})
    width = (if args.width? then args.width else 300) - margin.left - margin.right
    height = (if args.height? then args.height else 185) - margin.top - margin.bottom
    xpadding = (if args.xpadding? then args.xpadding else 1)

    x = d3.scale.linear()
      .domain([0, d3.max(args.values)])
      .range([0, width])

    nbins = Math.min(charts.count_freqs(args.values).length, 24)

    data = d3.layout.histogram()
      .bins(x.ticks(nbins))(args.values)

    max = d3.max(data, (d) -> d.y)

    y = d3.scale.linear()
      .domain([0, max])
      .range([height, 0])

    xAxis = d3.svg.axis().scale(x).orient('bottom')
      .ticks(Math.min(6, args.values.length))
    yAxis = d3.svg.axis().scale(y).orient('left')
      .ticks(Math.min(max, 6))

    svg = d3.select(args.selector).append('svg')
      .attr('class', 'chart')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .append('g')
      .attr('transform', "translate(#{margin.left}, #{margin.top})")

    svg.append("g")
      .attr("class", "y axis")
      .call(yAxis)

    bar = svg.selectAll(".bar")
      .data(data)
      .enter().append("g")
      .attr("class", "bar")
      .attr("transform", (d) -> "translate(#{x(d.x)}, 0)")

    bar.append("rect")
      .attr('x', xpadding)
      .attr('width', x(data[0].dx) - xpadding)
      .attr('y', height)
      .attr('height', 0)
      .transition()
        .delay((d, i) -> i * 200 / nbins)
        .attr('y', (d) -> y(d.y))
        .attr('height', (d) -> height - y(d.y))

    svg.append('g')
      .attr('class', 'x axis')
      .attr('transform', "translate(0, #{height})")
      .call(xAxis)
