/*
 * upload.js // 2019-12-30 Jani Tammi <jasata@utu.fi>
 */

/*****************************************************************************
 * 
 * Generic Functions and resources
 */
var getUrlParameter = function getUrlParameter(sParam)
// Returns either the value of the specified Query Parameter or undefined
// From: https://stackoverflow.com/questions/19491336/get-url-parameter-jquery-or-how-to-get-query-string-values-in-js
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
 * 
 * JSONForm specific functions
 */
// The entire JSONForm object
// Apparently cannot be recycled... and thus recreated every time.
var formObject = {};

// Object that tracks that both JSON sources are retrieved
// before createAlpaca() creates the form.
var externalData = {
    data:   null,
    schema: null
};


function clearForm()
{
    $('#fileForm').html('');
    $('#fileForm').removeClass(); // Remove all
    externalData.data   = null;
    externalData.schema = null;
    $('#fileForm').addClass('please-choose-file');
}

// Retrieves data and schema JSON from server
// before building AlpacaJS form.
function loadForm(id) {
    console.log("loadForm(" + id + ")...")
    // Wipe it clean
    clearForm();

    //
    // Initiate data query
    //
    const xhr_data = new XMLHttpRequest();
    // .onload() and .onerror() are modern
    // Do NOT use .onreadystatechange
    xhr_data.onload = function(e)
    // xhr.readyState === 4
    {
        if (this.status == 200) {
            externalData.data = JSON.parse(this.responseText);
            renderForm(externalData);
        } else {
            console.log("Status code " + this.status);
        }
    };
    xhr_data.onerror = function(e)
    // Network error!
    {
        console.log("xhr_data Network error! Status:" + this.status + ", readyState: " + this.readyState);
    };
    //xhr_data.addEventListener("load", loadData);
    //xhr_data.addEventListener("error", transferFailed);
    //xhr_data.addEventListener("abort", transferFailed);
    xhr_data.open('GET', '/api/file/' + id);
    xhr_data.send(); // with no payload, obviously

    //
    // Initiate schema query
    //
    const xhr_schema = new XMLHttpRequest();
    xhr_schema.onload = function(e) {
        if (this.status == 200) {
            externalData.schema = JSON.parse(this.responseText);
            renderForm(externalData);
        } else {
            console.log("xhr_schema Status code:" + this.status);
        }
    }
    xhr_data.onerror = function(e) {
        console.log("xhr_data Network error! Status:" + this.status + ", readyState: " + this.readyState);
    };
    xhr_schema.open('GET', '/api/file/schema');
    xhr_schema.send();
}




function renderForm(extData) {
    console.log("renderForm()");
    if (extData.data && extData.schema) {
        formObject = {};
        $.extend(formObject, form);
        $.extend(formObject, code);
        //$.extend(formObject, extData.data);
        formObject.value = extData.data.data;
        $.extend(formObject, extData.schema);
        //console.log(formObject);
        $('#fileForm').jsonForm(formObject);
    }
}




function onSubmitForm(formObj) {
    console.log("onSubmitForm()");
    var data = {};

    var x = $("#fileForm").serializeArray(); 
    $.each(x, function(i, field) {
        data[field.name] = field.value;
        /*
        data.push({
            key:   field.name,
            value: field.value
        });
        */
        
    });
    console.log(data);
    const xhr = new XMLHttpRequest();
    xhr.onload = function(e)
    {
        if (this.status == 200) {
            console.log("Successful PUT");
            clearForm();
        } else {
            console.log("Status code " + this.status);
        }
    };
    xhr.onerror = function(e)
    // Network error!
    {
        console.log("xhr Network error! Status:" + this.status + ", readyState: " + this.readyState);
    };
    xhr.open('PUT', '/api/file/' + data.id);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.send(JSON.stringify(data));



    // Must not let the HTML FORM do anything; return false
    return false;
}



///////////////////////////////////////////////////////////////////////////////
//
// DataTable helpers
//
function createLink(data, rowObj)
{
    return '<a onClick="return loadForm(' + rowObj.id + ');">' + data + '</a>';
}

// EOF
