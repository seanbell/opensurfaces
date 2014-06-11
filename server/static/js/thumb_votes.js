window.update_thumb_votes = function() {
$('.thumb-votes').each(function() {
	var $this = $(this);
	$this.removeClass('thumb-votes');
	var vals = $this.attr('data-votes').split(',');
	$this.text('');

	total = 0;
	for (var i = 0; i < 2; i ++) {
		vals[i] = Number(vals[i]);
		total += vals[i];
	}
	if (total === 0) { return; }

	w = [];
	for (var i = 0; i < 3; i ++) {
		w[i] = 100 * vals[i] / total;
	}

	$this.append('<div class="bar bar-success" style="width:' +
				w[0] + '%">' + vals[0] + '</div>');
	$this.append('<div class="bar bar-danger" style="width:' +
				w[1] + '%">' + vals[1] + '</div>');
});
};
