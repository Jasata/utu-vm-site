/*
 * VMUpload.js
 *
 * 2020-09-05   Initial version.
 * 2020-09-12   Development frozen for now...
 *
 *  Functional Description
 * 
 *      Step 1  File (HTML5 API object) is received on creation (consturctor).
 *              Parameters are extracted and saved.
 *      Step 2  Sent file name & size in a GET request for upload permission:
 *              200, {
 *                  'upid': <upid>,
 *                  'chunksize': <n bytes>,
 *                  'chunklist': [true, false, false, false]
 *              }
 *              OR
 *              400 : POST data does not match required format
 *              401 : Uploader is not a teacher
 *              406 : File not of any accepted type
 *              409 : File by that name already exists
 *              413 : File is larger than maximum allowed
 *      Step 3  Chunk is POST'ed to /api/upload/<upid>:
 *              chunkID: <ordinal>
 *              checksum: <crc32 or similar>
 *              file part, as in usual POSTs
 *              Server responses are: 202 Accepted or 406 (not acceptable)
 *              ONLY THE LAST CHUNK GETS STATUS CODE 200!!
 *
 * Events:
 *    vmuProgress
 *    vmuError
 *    vmuSuccess
 *
 *  USAGE:
 *      import { VMUpload } from "/js/vmupload.js";
 *          var vmup = new VMUpload(
 *              files[0],
 *              {
 *                   maxChunkRetries:    4
 *              }
 *          );
 */

/*
 * Constructor excepts two arguments:
 *      oFile       HTML5 File API object of type 'File'
 *      opts        Settings object (see defaults below)
 */
class VMUpload {
    defaults = {
        progressCallbacksInterval:  500,
        permissionAPI:              '/api/file/upload',
        uploadAPI:                  '/api/file/upload',
        maxChunkRetries:            0,    // 0 = unlimited
        permanentErrors:            [404, 413, 415, 500, 501],
        successStatuses:            [200, 201, 202]
    };
    // Permission id (only valid for the UID it was given to)
    // Retrieved (and re-retrieved) by getPermission()
    upid      = null;
    chunksize = null;
    lastchunk = null;

    constructor(oFile, opts) {
        this.opts = $.extend({}, this.defaults, opts || {});
        this.oFile = oFile;

        // Get upload permission {upid, chunksize, lastchunk}
        try {
            this.getPermission();
        } catch(e) {
            console.log("TODO: Trigger vmuError event!");
            throw "Upload permission could not be acquired!";
        }

    }



    getPermission() {
        let url =   this.opts.permissionAPI +
                    '?filename=' + this.oFile.name +
                    '&filesize=' + this.oFile.size;
        //Promise.resolve(
        $.when(
            $.ajax({
                context:        this,       // Super important!
                responseType:   'json',
                type:           'GET',
                url:            url,
                contentType:    false,
                cache:          false,
                processData:    false,
                error: function(xhr, error, errorThrown) {
                    console.log(
                        "VMUpload.getPermission(): .ajax() error " + xhr.status
                    );
                    throw errorThrown;
                },
                //success: function(data, textStatus, xhr) {
                complete: function(xhr, status) {
                    console.log(
                        "VMUpload.getPermission(): ajax() success"
                    );
                }
            }) /* $.ajax */
        ) /* $.when */
        .then(function(data, textStatus, xhr) {
            this.setPermission(xhr)
        });
    }

    // Callback for $.when($.ajax()).then() 
    setPermission(xhr) {
        try {
            this.upid       = xhr.responseJSON['upid'];
            this.chunksize  = xhr.responseJSON['chunksize'];
            this.lastchunk  = xhr.responseJSON['lastchunk'];
        } catch(err) {
            throw err.message;
        }
        this.nChunks = Math.ceil(this.oFile.size / this.chunksize);
        console.log(
            "VMUpload.setPermission(): File size: " + this.oFile.size + ", " +
            "Chunk size: " + this.chunksize + ", " +
            "Number of chunks: " + this.nChunks
        );

        // Ugly way to avoid async problems...
        // Chain calls like this:
        try {
            this.sendFile();
        } catch(e) {
            console.log("TODO: Trigger vmuError event!");
            console.log(e.message);
            throw "File upload failure";
        }
    }

    // Implementation that I could not get to work
    getPermission1() {
        // I can't see to get this to work... try another way?
        let url =   this.opts.permissionAPI +
                    '?filename=' + this.oFile.name +
                    '&filesize=' + this.oFile.size;
        console.log(url);
        const response = fetch( // removed await
            url,
            {
            method:         'GET',
            mode:           'same-origin',
            cache:          'no-cache',
            credentials:    'same-origin',  // So that cookies are sent
            redirect:       'error',        // Do not allow redirects
            referrerPolicy: 'no-referrer',
            }
        ).then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
        })
        .then(response => response.json()) // "Cannot read property 'json' of undefined"
        .then(data => {
            console.log(data);
        });
    }


    sendFile() {
        this.nChunks = Math.ceil(this.oFile.size / this.chunksize);
        console.log(
            "sendFile(): File size: " + this.oFile.size + ", " +
            "Chunk size: " + this.chunksize + ", " +
            "Number of chunks: " + this.nChunks
        );
        // Do not send last (successfully sent) chunk - send the next
        // If 'null' send chunk #0,
        // If 0, then send chunk #1
        // ...
        for (
            var i = (parseInt(this.lastchunk, 10) || -1) + 1;
            i < this.nChunks;
            i++
        ) {
            let from = i * this.chunksize;
            let to   = (i + 1) * this.chunksize - 1;
            to = to > this.oFile.size ? this.oFile.size : to;
            console.log(
                "Sending chunk " + i + ", from: " + from +
                ", to: " + to 
            );
            //let oBlob = this.oFile.slice(from, to);
            // TODO: Send blob
        }
        console.log(this.oFile.size);
    }

}


/* VMUploader.js */