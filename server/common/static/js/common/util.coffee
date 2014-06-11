# polygon fill colors
POLYGON_COLORS = [
  '#5D8AA8', '#3B7A57', '#915C83', '#A52A2A', '#FFE135',
  '#2E5894', '#3D2B1F', '#FE6F5E', '#ACE5EE', '#006A4E',
  '#873260', '#CD7F32', '#BD33A4', '#1E4D2B', '#DE6FA1',
  '#965A3E', '#002E63', '#FF3800', '#007BBB', '#6F4E37',
  '#0F4D92', '#9F1D35', '#B78727', '#8878C3', '#30D5C8',
  '#417DC1', '#FF6347'
]

# returns a url parameter in the querystring
window.getURLParameter = (name) ->
  decodeURIComponent((new RegExp("[?|&]#{name}=([^&;]+?)(&|##|;|$)").exec(location.search) || [null,""] )[1].replace(/\+/g, '%20'))||null

# sets the button state
set_btn_enabled = (selector, enabled = true) ->
  #console.log "set_btn_enabled(#{selector}, #{enabled})"
  if enabled
    $(selector).removeAttr('disabled')
  else
    $(selector).attr('disabled', 'disabled')

# returns all unique values in the array, keeping original order
unique_array = (list) ->
  set = {}
  ret = []
  for value in list
    if value not of set
      set[value] = true
      ret.push(value)
  return ret

# choose a photo url from a set such that it best fits within 'size'
select_image_url = (urls, size) ->
  best_k = 65536
  best_v = urls.orig
  for k, v of urls when k != 'orig'
    k = Number(k)
    if k >= size and k < best_k
      best_k = k
      best_v = v
  #console.log "size: #{size}, best_k: #{best_k}"
  return best_v

# add a GET parameter to the URL to ensure that we aren't served a cached
# non-CORS version
get_cors_url = (url) ->
  if url.indexOf('?') == -1
    url + '?origin=' + window.location.host
  else
    if url.indexOf("?origin=") == -1 and url.indexOf("&origin=") == -1
      url + '&origin=' + window.location.host
    else
      url

# load a cross-origin image
load_cors_image = (url, onload=null) ->
  img = new Image()
  img.crossOrigin = ''
  if onload?
    img.onload = onload
  img.src = get_cors_url(url)
  return img

# load an image and fire an event when complete
load_image = (url, onload=null) ->
  img_obj = new Image()
  if onload?
    img_obj.onload = ->
      onload(img_obj)
  img_obj.src = url
  return img_obj

# load several images and fire an event when complete
load_images = (urls, onload=null) ->
  count = 0
  image_objs = []
  console.log "load_images: #{count}/#{urls.length}"
  for url in urls
    image_objs.push(load_image(url, ( ->
      count += 1
      console.log "load_images: loaded #{url} (#{count}/#{urls.length})"
      if onload? and count == urls.length
        onload(image_objs)
    )))
  return image_objs

# compute width, height so that obj fills a box.
# the object is only blown up by at most max_scale.
# there is no limit to how much it must be shrunk to fit.
compute_dimensions = (obj, bbox, max_scale = 2) ->
  scale_x = bbox.width / obj.width
  scale_y = bbox.height / obj.height
  if scale_x < scale_y
    if scale_x < max_scale
      return {
        width: bbox.width
        height: obj.height * scale_x
        scale: scale_x
      }
  else
    if scale_y < max_scale
      return {
        width: obj.width * scale_y
        height: bbox.height
        scale: scale_y
      }

  return {
    width: obj.width * max_scale
    height: obj.height * max_scale
    scale: max_scale
  }

# stops an event from propagating
stop_event = (e) ->
  e ?= window.event
  e.stopPropagation?()
  e.preventDefault?()
  e.cancelBubble = true
  e.returnValue = false
  e.cancel = true
  false


# debounce events (e.g. for resize events)
debounce = (func, timeout=200) ->
  timeoutID = null
  return ((args...) ->
    scope = this
    if timeoutID?
      clearTimeout(timeoutID)
    timeoutID = setTimeout(( ->
      func.apply(scope, args)
    ), timeout)
  )


# from http://mjijackson.com/2008/02/rgb-to-hsl-and-rgb-to-hsv-color-model-conversion-algorithms-in-javascript
# assumes r, g, b are in [0, 255] and h, s, v are in [0, 1]
rgb_to_hsv = (r, g, b) ->
  r = r / 255
  g = g / 255
  b = b / 255

  max = Math.max(r, g, b)
  min = Math.min(r, g, b)
  v = max
  d = max - min
  s = (if max is 0 then 0 else d / max)
  if max is min
    h = 0 # achromatic
  else
    switch max
      when r
        h = (g - b) / d + ((if g < b then 6 else 0))
      when g
        h = (b - r) / d + 2
      when b
        h = (r - g) / d + 4
    h /= 6
  [h, s, v]

# from http://mjijackson.com/2008/02/rgb-to-hsl-and-rgb-to-hsv-color-model-conversion-algorithms-in-javascript
# assumes r, g, b are in [0, 255] and h, s, v are in [0, 1]
hsv_to_rgb = (h, s, v) ->
  i = Math.floor(h * 6)
  f = h * 6 - i
  p = v * (1 - s)
  q = v * (1 - f * s)
  t = v * (1 - (1 - f) * s)
  switch i % 6
    when 0
      r = v
      g = t
      b = p
    when 1
      r = q
      g = v
      b = p
    when 2
      r = p
      g = v
      b = t
    when 3
      r = p
      g = q
      b = v
    when 4
      r = t
      g = p
      b = v
    when 5
      r = v
      g = p
      b = q
  [r * 255, g * 255, b * 255]
