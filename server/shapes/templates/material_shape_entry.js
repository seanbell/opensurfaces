{
id: {{ c.id }},
url_square_300: "{{ c.image_square_300.url }}",
vertices: [{{ c.vertices }}],
triangles: [{{ c.triangles }}],
segments: [{{ c.segments }}],
{% if c.dominant_rgb0 %}dominant_rgb0: "{{ c.dominant_rgb0 }}",{% endif %}
{% if c.image_bbox %}image_bbox: "{{ c.image_bbox_1024.url }}",{% endif %}
photo: { id: {{ c.photo.id }}, url: "{{ c.photo.image_1024.url }}", {% if c.photo.fov %}fov: {{ c.photo.fov }}{% endif %}, {% if include_uvn_matrices %}uvn_matrices: {{ c.photo.vanishing_uvn_matrices_json }}{% endif %}  },
}
