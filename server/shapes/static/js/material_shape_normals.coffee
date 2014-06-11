$(->
  $('.shape-normal').each( ->
    $this = $(this)
    display = new NormalDisplay(
      container_id: $this.attr('id')
      direction: $this.attr('data-theta')
      tilt: $this.attr('data-phi')
      width: 152
      height: 152
      radius: 50
    )
  )
)
