# Passive display of objects
# ... TODO

class DisplayStage
  constructor: (args) ->

  create_stage: ->
    # create stage
    @stage = new Kinetic.Stage(
      container: args.container_id,
      width: @size.width, height: @size.height)
    @layer = new Kinetic.Layer()
    @stage.add(@layer)
