/*
 * edit_vm_details.js - Jani Tammi <jasata@utu.fi>
 * JSONForm scripts for edit_vm_details.html.
 *
 *  2020-08-30  Initial version.
 *  2020-09-23  Add byte size handling (kB, MB, GB...)
 *
 *  REQUIRES A <FORM ID="fileForm">
 */

// Where to return on "Cancel" and successful save
var parent_url = "/upload.html";

// JSONForm.js presentation ///////////////////////////////////////////////////
// Defines the fields that are rendered; how and in which order
// This file may not really an ideal place for format/presentation information,
// but since this most definitely does NOT belong to API (like schema and data)
// ...this will be here for now.
//
// In some far distant future, the database MIGHT contain configurable
// presentation information, but the wisdom of doint that for this form is
// questionable at the best - this is not going to change so often!
form = {
    "form": [
        {
            "key":          "id",
            "type":         "hidden"
        },
        {
            "key":          "name",
            "title":        "File Name",
            "readonly":     true
        },
        {
            "key":          "size",
            "title":        "File Size",
            "readonly":     true
        },
        {
            "key":          "sha1",
            "title":        "File Checksum (SHA1)",
            "readonly":     true,
            "placeholder":  "Checksum will be calculated automatically later..."
        },
        {
            "key":          "label",
            "title":        "Label",
            "description":    "Descriptive name for this virtual machine"
        },
        {
            "key":          "ostype",
            "title":        "Operating System",
            "placeholder":  "'Debian 10 64-bit' or 'FreeDOS 1.2' for example."
        },
        {
            "key":          "type",
            "title":        "File Type",
            "titleMap": {
                "vm":   "Virtual Machine image",
                "usb":  "Bootable USB-stick image"
            }
        },
        {
            "key":          "version",
            "title":        "Version",
            "placeholder":  "Version number, date or similar"
        },
        {
            "key":          "dtap",
            "title":        "Status",
            "titleMap": {
                "development":  "Development Version",
                "testing":      "Testing Version",
                "acceptance":   "Version for Acceptance Testing",
                "production":   "Production Version"
            }
        },
        {
            "key":          "ram",
            "title":        "RAM",
            "description":  "Allocated memory",
            "minimum":      1,
            "description":  "2 GB, 2048 MB, or 2097152, for example"
        },
        {
            "key":          "cores",
            "title":        "CPU Cores",
            "description":  "Allocated number processor cores"
        },
        {
            "key":          "disksize",
            "title":        "Disk Size",
            "description":  "Required disk space for students to run this VM"
        },
        {
            "key":          "downloadable_to",
            "title":        "Downloadable to",
            "description":  "Sets the minimum privilege level to be able to download",
            "titleMap": {
                "nobody":   "NOT AVAILABLE",
                "anyone":   "Available to anyone",
                "student":  "All university account holders",
                "teacher":  "Only teachers"
            }
        },
        {
            "key":          "description",
            "title":        "Description",
            "type":         "textarea",
            "placeholder":  "Up to 300 characters"
        },
        {
            "type":         "help",
            "helpvalue":    "<strong>Click on <em>Save</em></strong> when you're done"
        },
        {
            "type":         "submit",
            "title":        "Save"
        },
        {
            "type":         "button",
            "title":        "Cancel",
            "onClick":      function (event) {
                event.preventDefault();
                location.replace(parent_url);
            }
        }
    ]
};
code = {
    onBeforeRender: function (data, node) {
        // Compute the value of "myvalue" here
        if (['ram', 'disksize'].includes(data.keydash)) {
            data.value = formatBytes(data.value, 0);
        }
    }
};


function formatBytes(bytes, decimals = 2)
{
   if (bytes == null) return bytes;
   if (isNaN(bytes)) return bytes;
   if (typeof bytes === 'string' && bytes.trim() == '') return bytes;
   if (bytes === 0) return '0 Bytes';

    const k = 1024;
    var dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    // No decimals for Bytes
    if (i == 0) dm = 0;
    return (bytes / Math.pow(k, i)).toFixed(dm) + ' ' + sizes[i];
}

/*****************************************************************************
 * 
 * JSONForm specific functions
 */
// The entire JSONForm object
// Apparently cannot be recycled... and thus recreated every time.
var formObject = {};

// Object that tracks that both JSON sources (DATA and SCHEMA)
// are retrieved before form is created/rendered.
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



function renderForm(extData) {
    console.log("edit_vm_details.js:renderForm()");
    if (extData.data && extData.schema) {
        formObject = {};
        $.extend(formObject, form);
        $.extend(formObject, code);
        //$.extend(formObject, extData.data);
        formObject.value = extData.data.data;
        $.extend(formObject, extData.schema);
        $('#fileForm').jsonForm(formObject);
    }
}




// loadForm() /////////////////////////////////////////////////////////////////
// Retrieves DATA and SCHEMA (in JSON) from server.
// Because of the asyncronous nature of the requests,
// an utility function renderForm() is created, which tracks when both
// schema and data have arrived, and only then renderes the form.
function loadForm(id) {
    console.log("edit_vm_details.js:loadForm(" + id + ")...");
    // Wipe it clean
    clearForm();



    //
    // Initiate DATA query
    //
    const xhr_data = new XMLHttpRequest();
    // .onload() and .onerror() are modern
    // Do NOT use .onreadystatechange

////// onLoad handler
    xhr_data.onload = function(e)
    // xhr.readyState === 4
    {
        if (this.status == 200) {
            externalData.data = JSON.parse(this.responseText);
            renderForm(externalData); // look into this .js for this function
        } else {
            console.log("edit_vm_details.js:loadForm(): Status code: " + this.status);
        }
    };

////// onError handler
    xhr_data.onerror = function(e)
    // Network error!
    {
        console.log("edit_vm_details.js:loadForm(): xhr_data Network error! Status:" + this.status + ", readyState: " + this.readyState);
    };

////// Unused events
    //xhr_data.addEventListener("load", loadData);
    //xhr_data.addEventListener("error", transferFailed);
    //xhr_data.addEventListener("abort", transferFailed);


////// Send GET request for DATA
    xhr_data.open('GET', '/api/file/' + id);
    xhr_data.send(); // with no payload, obviously



    //
    // Initiate schema query
    //
    const xhr_schema = new XMLHttpRequest();

////// onLoad handler
    xhr_schema.onload = function(e) {
        if (this.status == 200) {
            externalData.schema = JSON.parse(this.responseText);
            renderForm(externalData);
        } else {
            console.log("edit_vm_details.js:loadForm(): xhr_schema Status code:" + this.status);
        }
    }

////// onError handler
    xhr_data.onerror = function(e) {
        console.log("edit_vm_details.js:loadForm(): xhr_data Network error! Status:" + this.status + ", readyState: " + this.readyState);
    };

////// Send GET request for schema
    xhr_schema.open('GET', '/api/file/schema');
    xhr_schema.send();
}




// onSubmitForm ///////////////////////////////////////////////////////////////
/* Called by <FORM OnSubmit>
 *
 *  
 */
function onSubmitForm(formObj) {
    console.log("edit_vm_details.js:onSubmitForm()");
    var data = {};

////// Pack data into an array
    var x = $("#fileForm").serializeArray(); 
    $.each(x, function(i, field) {
        data[field.name] = field.value;
    });
    console.log(data);


    const xhr = new XMLHttpRequest();
    xhr.onload = function(e)
    {
        if (this.status == 200) {
            console.log("edit_vm_details.js:onSubmitForm(): Successful PUT");
            //clearForm();
            //window.location.href = url_success;
            location.replace(parent_url);
        } else {
            console.log("edit_vm_details.js:onSubmitForm(): PUT Failed! Status code: " + this.status);
        }
    };
    xhr.onerror = function(e)
    // Network error!
    {
        console.log("edit_vm_details.js:onSubmitForm(): xhr Network error! Status:" + this.status + ", readyState: " + this.readyState);
    };
    xhr.open('PUT', '/api/file/' + data.id);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.send(JSON.stringify(data));


    // Must not let the HTML FORM do anything; return false
    return false;
}