# NO LONGER USED
# this is all done in SVG server-side now

$ ->
  on_items_added = ->
    pending_count = 0
    flush_thresh = 2
    $(".entry-new").removeClass("entry-new").each( ->
      $this = $(this)
      model = $this.attr('data-model')
      window.model_registry[model]?.new_item?($this)

      # count how many are pending -- we don't want too many
      # pending at once, so we flush the list every so often.
      pending_count += 1
      if pending_count >= flush_thresh
        flush_thresh *= 2
        pending_count = 0
        window.fetch_entry_data()
    )
    window.fetch_entry_data()
    true
  $(document).on("items-added", on_items_added)
  on_items_added()

# add the id to the list of ids that we want to fetch.
# the fetching is done in fetch_entry_data.
window.pending_entry_data = (model, id, on_success) ->
  if model? and id? and on_success?
    reg = window.model_registry[model]
    cache = reg.cache
    if cache[id]?
      on_success(cache[id])
    else
      reg.pending.push(
        id: id,
        on_success: on_success
      )

# actually fetch the data we want.  there is one GET
# request per model.
window.fetch_entry_data = ->
  # recursively fix up data sent from server
  parse_json = (obj) ->
    if typeof(obj) != 'object'
      obj
    else
      ret = {}
      for k,v of obj
        if k == 'vertices' or k == 'triangles' or k == 'segments'
          ret[k] = (Number(x) for x in v.split(','))
        else if k == 'uvnb'
          ret[k] = JSON.parse(v)
        else
          ret[k] = parse_json(v)
      ret

  for model, reg of window.model_registry
    if reg.pending.length == 0
      continue

    do (model, reg) ->
      cache = reg.cache
      pending = reg.pending

      # gather pending IDs
      ids = []
      callback = {}
      while pending.length > 0
        p = pending.pop()
        ids.push(p.id)
        if callback[p.id]?
          callback[p.id].push(p.on_success)
        else
          callback[p.id] = [p.on_success]
      ids.sort()

      # do the fetch
      $.ajax("/entry-ajax/#{model}/",
        type: 'GET'
        data:
          ids: ids.join('-')
        success: (data) ->
          for id in ids
            obj = parse_json(data.objects[id])
            cache[id] = obj
            for f in callback[id]
              f?(obj)
          true
        error: ->
          console.log "Error fetching #{model}/#{id}"
      )


window.register_model = (args) ->
  if not window.model_registry?
    window.model_registry = {}
  window.model_registry[args.model] =
    model: args.model
    prepare_item: args.prepare_item
    new_item: (t) ->
      pending_entry_data(args.model, t.attr('data-id'), (obj) ->
        args.prepare_item(t, obj)
      )
    cache: {}
    pending: []

do ->
  find_size = (t) ->
    wrapper = t.find('.overlay-wrapper')
    if wrapper.length == 0
      wrapper = t.closest('.overlay-wrapper')
    if wrapper.length == 0
      return 0
    else
      return wrapper.width()

  prepare_shape = (t, shape) ->
    $pd = t.find('.pd')
    if ($pd? and $pd.length > 0)
      add_display = ->
        size = find_size(t)
        $pd.empty()
        new PolyDisplayFill(
          container_id: $pd[0],
          width: size, height: size,
          photo_url: select_image_url(shape.photo.image, 1024),
          vertices: shape.vertices,
          triangles: shape.triangles,
          segments: shape.segments,
        )
      add_display()
      #$(window).on('resize', add_display)

  prepare_normal = (t, normal) ->
    $nd = t.find('.nd')
    if ($nd? and $nd.length > 0)
      add_display = ->
        size = find_size(t)
        $nd.empty()
        new NormalController(
          container_id: $nd[0],
          width: size, height: size,
          uvnb: normal.uvnb,
          shape: normal.shape
        )
      add_display()
      #$(window).on('resize', add_display)

  window.register_model(
    model: 'shapes/shaperectifiednormallabel',
    prepare_item: (t, obj) ->
      prepare_shape(t, obj.shape)
      prepare_normal(t, obj)
  )

  window.register_model(
    model: 'shapes/shapebsdflabel_wd',
    prepare_item: (t, obj) ->
      prepare_shape(t, obj.shape)
  )

  window.register_model(
    model: 'shapes/materialshape',
    prepare_item: (t, obj) ->
      prepare_shape(t, obj)
  )
