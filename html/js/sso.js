/*
 * sso.js - Jani Tammi <jasata@utu.fi>
 *
 *  0.1.0   2019-12-22  Initial version.
 *  0.2.0   2019-12-22  State and visuals now one and the same
 *  0.3.0   2019-12-22  Remove ::after and compact design
 *  0.4.0   2019-12-23  CANNOT USE Flask session! REST API model implemented
 *  0.5.0   2019-12-23  Domain-SSO redirect added
 *  0.6.0   2019-12-23  Clean out unnecessary debug messages
 *
 * NOTE:    Flask session cookie is HTTPOnly!
 *          I cannot access it...
 *
 *
 * // Returns path only (/path/example.html)
 * var pathname = window.location.pathname;
 *
 * // Returns full URL (https://example.com/path/example.html)
 * var url = window.location.href;
 *
 * // Returns base URL (https://example.com)
 * var origin = window.location.origin;
 */

jQuery.fn.sso = function(options)
{
    var _this = this;
    // Build the widget
    $(_this).html("<div><a>Loading...</a></div>");
    console.log("sso.init() called")


      //
/////// onClick handler function
    //
    $(_this).click(function()
    {
        console.log("Element click()")
        if ($("#sso").hasClass('deactivated'))
        {
            console.log("Deactive element, returning...")
            return;
        }
        // Passivate element (removed by 'updateState' handler)
        $("#sso").addClass('deactivated');

        if ($("#sso").hasClass('anonymous'))
        {
            // direct broser to SSO login page
            window.location.href = "https://sso.utu.fi/sso/XUI/#login/&goto=https%3A%2F%2Fvm.utu.fi%3A443%2Fsso%2flogin%3Fdestination%3D" + encodeURIComponent(window.location.pathname);
        }
        else
        {
            // direct browser to sso/logout
            $.ajax({
                url:        '/sso/logout',
                type:       'GET',
                success: function(data, textStatus, xhr) {
                    console.log('/sso/logout HTTP Request status: ' + xhr.status);
                    $("#sso").trigger('updateState');
                },
                complete: function(xhr, textStatus) {
                    console.log('/sso/logout HTTP Request status: ' + xhr.status);
                } 
            });
        }
    });


      //
/////// updateState handler function
    //
    $(_this).on('updateState', function(event) {
        // Launch an Ajax query and trigger event to updateState
        $.getJSON(window.location.origin + '/sso/state', function(data) {
            console.log(".getJSON() success, role: " + data.role);
        }).done(function(data) {
            console.log(".getJSON().done(), role: " + data.role);
            // NOTE: If 'this' is used, inner HTML vanishes! (don't know why)
            $("#sso").removeClass(); // Remove all
            $("#sso").addClass(data.role);
            if (data.role == 'anonymous')
                $("#sso a").text("Login");
            else
                $("#sso a").text("Logout");
        })
        .fail(function(jqxhr, textStatus, error) {
            var err = textStatus + ", " + error;
            console.log(".getJSON().fail()" + err);
        })
         .always(function() {
            console.log( ".getJSON.always()" );
         });
    });

    //
    // Element has been built, trigger state (and visual) update
    //
    $(_this).trigger('updateState');

    return _this;
}

// EOF
