/*
 * upload_process.js - Jani Tammi <jasata@utu.fi>
 * Script library for upload_process.html.
 *
 *  2020-09-09  Initial version.
 *
 * Good read about async problems:
 * https://stackoverflow.com/questions/14220321/how-do-i-return-the-response-from-an-asynchronous-call?noredirect=1&lq=1
 */


// All this function needs to know is that if the return code is 200,
// there is no name conflict...
function isFreeName(flowid, filename) {
    flowProcessAPI = `/api/file/flow/${flowid}/store/?name=${filename}`;
    var jqXHR = $.ajax({
        xhr: function() {
            var xhr = new window.XMLHttpRequest();
            return xhr;
        },
        async:          false,
        type:           'GET',
        url:            flowProcessAPI,
        contentType:    false,
        cache:          false,
        processData:    false
    });
    //console.log(jqXHR); //.responseText);
    return jqXHR.status == 200;
}

function saveFile(flowid, filename) {
    flowProcessAPI = `/api/file/flow/${flowid}/store`;
    let formData = new FormData();
    formData.append('name', filename);
    var jqXHR = $.ajax({
        xhr: function() {
            var xhr = new window.XMLHttpRequest();
            return xhr;
        },
        async:          false,
        type:           'POST',
        url:            flowProcessAPI,
        data:           formData,
        contentType:    false,
        cache:          false,
        processData:    false
    });
    console.log(`savaFile(): xhr.status: ${jqXHR.status}`);
    return jqXHR.status == 200;
}

/* EOF */