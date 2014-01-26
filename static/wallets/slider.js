//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU Affero General Public License
// version 3 as published by the Free Software Foundation.
//
// This program is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
// General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
// USA
//
// Authors:
// Caner Candan <caner@candan.fr>, http://caner.candan.fr
// Geraldine Starke <geraldine@starke.fr>, http://www.vegeclic.fr
//

$(function() {
    var sliders = $("#sliders .slider");
    var availableTotal = parseInt($('#available_total').val());

    sliders.each(function() {
	var s = $(this);
	var coin_value = parseInt(s.parent().find('.coin_value').val());
	var max_value = parseInt(s.parent().find('.max_value').val());

	s.empty().slider({
	    value: 0,
	    min: 0,
	    max: max_value,
	    range: "max",
	    step: 1,
	    coin: coin_value,
	    animate: false,

	    stop: function(event, ui) {
		// Get current total
		var total = 0;
		sliders.not(this).each(function() {
		    total += $(this).slider('option', 'value') * $(this).slider('option', 'coin');
		});

		var value = $(this).slider('option', 'value');

		if ((total + (value*coin_value)) > (availableTotal)) {
		    value = parseInt((availableTotal-total)/coin_value);
		}

		total += value * coin_value;

		$(this).slider('option', 'value', value);
		$(this).siblings().find('.quantity').text(value);
		$(this).siblings().find('.equal').text(value*coin_value);
		$(this).siblings('.input_value').val(value);

		$('#sliders_total').text(total);
		$('#remains').text(availableTotal-total);
	    },

	    slide: function(event, ui) {
		// Get current total
		var total = 0;
		sliders.not(this).each(function() {
		    total += $(this).slider('option', 'value') * $(this).slider('option', 'coin');
		});

		if ((total + (ui.value*coin_value)) > (availableTotal)) {
		    ui.value = parseInt((availableTotal-total)/coin_value);
		}

		// Need to do this because apparently jQ UI
		// does not update value until this event completes
		total += ui.value * coin_value;

		// Update display to current value
		$(this).siblings().find('.quantity').text(ui.value);
		$(this).siblings().find('.equal').text(ui.value*coin_value);
		$(this).siblings('.input_value').val(ui.value);

		$('#sliders_total').text(total);
		$('#remains').text(availableTotal-total);
	    }
	});
    });

    var initialize = function() {
	var total = 0;
	sliders.each(function() {
	    $(this).slider('value', 0);
	    $(this).siblings().find('.quantity').text(0);
	    $(this).siblings().find('.equal').text(0);
	    $(this).siblings('.input_value').val(0);
	});
	$('#sliders_total').text(0);
	$('#remains').text(availableTotal);
    };

    var randomize = function() {
 	initialize();

	var total = 0
	sliders.each(function() {
	    if (total >= availableTotal) { return; }

	    var value = $(this).slider('option', 'value');
	    var max = $(this).slider('option', 'max');
	    var coin = $(this).slider('option', 'coin');

	    max = (availableTotal-total)/coin;

	    var sol = (coin > 1) ? parseInt(Math.random()*max) : max;
	    total += sol*coin;

	    $(this).slider('value', sol);
	    $(this).siblings().find('.quantity').text(sol);
	    $(this).siblings().find('.equal').text(sol*coin);
	    $(this).siblings('.input_value').val(sol);
	});

	$('#sliders_total').text(total);
	$('#remains').text(availableTotal-total);
    };

    $('#init').click(initialize);
    $('#random').click(randomize);

    randomize();
});

function create_one_slider(choices, id, default_value, disabled) {
    $('#' + id + '-slide').slider({
	range: 'max',
	min: 0,
	max: choices.length-1,
	value: default_value,
	disabled: disabled,
	slide: function( event, ui ) {
	    var i = parseInt(ui.value);
	    var v = choices[i];
	    $('#id_' + id)[0].selectedIndex = i;
	    $('#id_' + id).change();
	    $('#' + id + '-slide-text').text( v[1] );
	}
    });

    var i = parseInt($('#' + id + '-slide').slider('value'));
    var v = choices[i];
    $('#id_' + id)[0].selectedIndex = i;
    $('#id_' + id).change();
    $('#' + id + '-slide-text').text( v[1] );
}

$(function() {
    $('.slidebar-select').each(function() {
	var s = $(this)[0];
	var options = [];
	$(this).find('option').each(function() { options.push([$(this).val(), $(this).text()]); });
	create_one_slider(options, s.name, s.selectedIndex, $(this).hasClass('disabled'));
	$(this).hide();
    });
});
