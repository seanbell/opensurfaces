# UI for a normal
class NormalDisplay
  constructor: (args) ->
    @direction = args.direction
    @tilt = args.tilt
    @width = args.width || 210
    @height = args.height || 210
    @x = args.x || args.width / 2
    @y = args.y || args.height / 2
    @radius = args.radius || 50

    console.log @
    console.log args.container_id

    @stage = new Kinetic.Stage(
      container: args.container_id,
      width: @width,
      height: @height)
    @layer = new Kinetic.Layer()
    @stage.add(@layer)

    @update()

  update: ->
    @tilt = Math.min(Math.max(@tilt, 0), 0.5 * Math.PI)
    w = Math.max(Math.cos(@tilt) * @radius, 0)
    x2 = @x + Math.sin(@tilt) * Math.cos(@direction) * @radius * 0.5
    y2 = @y - Math.sin(@tilt) * Math.sin(@direction) * @radius * 0.5

    if not @ellipse?
      @ellipse = new Kinetic.Ellipse(
        x: @x
        y: @y
        fill: '#3c77cc'
        stroke: 'black'
        strokeWidth: 2
        width: w
        height: @radius
        rotation: -@direction
        opacity: 0.5
      )
      @layer.add(@ellipse)
    else
      @ellipse.setWidth(w)
      @ellipse.setRotation(-@direction)
      @ellipse.setPosition(@x, @y)
    @ellipse.moveToTop()

    if not @line?
      @line = new Kinetic.Line(
        points: [@x, @y, x2, y2],
        stoke: 'black',
        strokeWidth: 2,
        lineCap: 'round',
        lineJoin: 'round',
      )
      @layer.add(@line)
    else
      @line.setPoints([@x, @y, x2, y2])
    @line.moveToTop()

    @layer.draw()
