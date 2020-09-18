/*
 * upload.js - Jani Tammi <jasata@utu.fi>
 * Script library for upload.html and edit_vm_details.html pages.
 *
 *  2019-12-30  Initial version.
 *  2020-08-30  Supports now separate upload and edit pages.
 *  2020-08-30  JSONForm related code moved to edit_vm_details.js.
 *  2020-09-02  General functions moved to 'common.js'.
 *  2020-09-18  Add .ISO to allowed upload file extensions.
 *
 *
 */
// LOWER CASE ONLY!
var allowedExtensions = [
    'ova',
    'img',
    'zip',
    'iso'
];

// For UI messages telling the allowed extensions
// Prefixes each extension with a dot for better clarity
function dzExtList() {
    return allowedExtensions.map(el => '.' + el).join(", ");
}

// File type validation by extension
// return true for accepted file type, false otherwise
// Argument must be filename string
function validFileType(sFileName) {
    //console.log("oFileInput.value: " + oFileInput.value);
    //var sFileName = oFileInput.value;
    console.log("Checking filename : '" + sFileName + "'");
    if (sFileName.length > 0 && sFileName.indexOf('.') >= 0) {
        // ""       --> ""
        // "name"   --> ""
        // "f.txt"  --> "txt"
        // ".git"   --> ""
        // "a.b.c"  --> "c"
        var sExt = sFileName.slice((sFileName.lastIndexOf(".") - 1 >>> 0) + 2);
        console.log("validFileType(): File extension: '" + sExt + "'");
        if (allowedExtensions.includes(sExt.toLowerCase())) {
            console.log("validFileType(): true");
            return true;
        }
    }
    console.log("validFileType(): false");
    return false;
}


// This should be equal to $("#dz-file-input").val('');
function clearFileInput(oFileInput) {
    console.log("arg type : " + (typeof oFileInput));
    if (oFileInput.value) {
        // for modern browers
        try {
            oFileInput.value = '';
        } catch(err)
        { }
        // For obsolete browsers
        if (oFileInput.value) {
            var form = document.createElement('form'),
                parentNode = oFileInput.parentNode,
                ref = oFileInput.nextSibling;
            form.appendChild(oFileInput);
            form.reset();
            parentNode.insertBefore(oFileInput, ref);
        }
    }
}


function openEditVMPage(id)
{
    // TODO: Check if upload is in progress and warn about it
    location.replace('/edit_vm_details.html?id=' + id);
}


// EOF
