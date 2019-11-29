const slider = $('#sl2').slider({
  formatter: function(value) {
    return 'Current value: ' + value;
  }
});

slider.on('slideStop', function(e) {
  console.log('value = ' + e.value);
})(jQuery);