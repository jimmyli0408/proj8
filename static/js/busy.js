/**
 * Bind together javascript libraries used in this application.
 * Compile these with 'browserify' to create a combined, 'minified' 
 * version.  (See Makefile)
 */
/*
"use strict";
var moment = require('moment');
var daterangepicker = require('bootstrap-daterangepicker');

window.moment = moment;
window.daterangepicker = daterangepicker;
*/

$(document).ready(function() {
    
    $('input[name="daterange"]').daterangepicker({
        locale: { format: 'MM/DD/YYYY'},
    });
    $('input[name="daterange"]').val($('input[name="daterangevalue"]').val());
});
