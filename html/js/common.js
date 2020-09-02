/*
 * common.js - Jani Tammi <jasata@utu.fi>
 * Generic Functions
 *
 *  0.1.0   2020-09-02  Initial version.
 *
 *
 */

/*****************************************************************************
 * getUrlParameter() - Retrieve value of specified URL parameter
 *
 * Returns either the value of the specified Query Parameter or undefined
 * From: https://stackoverflow.com/questions/19491336/get-url-parameter-jquery-or-how-to-get-query-string-values-in-js
 */
var getUrlParameter = function getUrlParameter(sParam)
{
    var sPageURL = window.location.search.substring(1),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : decodeURIComponent(sParameterName[1]);
        }
    }
};


/*****************************************************************************
 * secondsToStr() - int seconds to FLOOR'ed human readable duration string.
 *
 * Examples:
 *      61          "1 minute"
 *      70000000    "2 years"
 */
function secondsToStr (temp) {
    function pluralize(unit, amount) {
        return amount + ' ' + unit + (amount > 1) ? 's' : '';
    }
    var years = Math.floor(temp / 31536000);
    if (years) {
        return pluralize('year', years);
    }
    var days = Math.floor((temp %= 31536000) / 86400);
    if (days) {
        return pluralize('day', days);
    }
    var hours = Math.floor((temp %= 86400) / 3600);
    if (hours) {
        return pluralize('hour', hours);
    }
    var minutes = Math.floor((temp %= 3600) / 60);
    if (minutes) {
        return pluralize('minute', minutes);
    }
    var seconds = temp % 60;
    return pluralize('second', seconds);
}




/*****************************************************************************
 * formatBytes() - int bytes to human readable size string.
 *
 * Examples:
 *      formatBytes(61123, 0)           "59 KB"
 *      formatBytes(702000000)          "669,47 MB"
 */
function formatBytes(bytes, decimals = 2)
// https://stackoverflow.com/questions/15900485/correct-way-to-convert-size-in-bytes-to-kb-mb-gb-in-javascript
{
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    var dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    // No decimals for Bytes
    if (i == 0) dm = 0;
    return (bytes / Math.pow(k, i)).toFixed(dm) + ' ' + sizes[i];
}



/* EOF */