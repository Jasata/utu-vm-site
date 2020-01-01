/*
 * sso.js - Jani Tammi <jasata@utu.fi>
 *
 *  0.1.0   2019-12-22  Initial version.
 *  0.2.0   2019-12-22  State and visuals now one and the same
 *  0.3.0   2019-12-22  Remove ::after and compact design
 *  0.4.0   2019-12-23  CANNOT USE Flask session! REST API model implemented
 *  0.5.0   2019-12-23  Domain-SSO redirect added
 *  0.6.0   2019-12-23  Clean out unnecessary debug messages
 *  0.7.0   2019-12-25  Add 'stateChanged' event for pages
 *  0.8.0   2010-01-01  API endpoints now under /api/sso
 *
 *  HOW TO USE
 *
 *      Include CSS and Javascript files in your HTML:
 *
 *          <link rel="stylesheet" href="css/sso.css">
 *          <script src="js/sso.js"></script>
 *
 *      Add somewhere a Login/Logout element (must have ID="sso"):
 *
 *          <div id="sso"></div>
 *
 *      Build the SSO Login/Logout element after page has loaded:
 *
 *          <script>
 *              $(document).ready(function() {
 *                  $("#sso").sso();
 *                  // ... other start-up code
 *              });
 *          </script>
 *
 *  NOTE: Obviously, a server side endpoints are also required...
 * 
 *
 *
 *  Offers 'stateChanged' event for pages to handle. It is triggered after the
 *  SSO session state is read from the server. For example:
 *
 *      $("#sso").on("stateChanged", function(event) {
 *          $("#vm_table").DataTable().ajax.reload(null, false);
 *          $("#usb_table").DataTable().ajax.reload(null, false);
 *      });
 *
 *
 */

jQuery.fn.sso = function(options)
{
    var _this = this;
    // Deactivate - reactivates once state has been read.
    $("#sso").addClass('deactivated');
    // Add inner HTML
    $(_this).html("<div><a>Loading...</a></div>");


      //
/////// onClick handler function
    //
    $(_this).click(function()
    {
        if ($("#sso").hasClass('deactivated'))
        {
            console.log("Deactive element, returning...")
            return;
        }
        // Passivate element (removed by 'updateState' handler)
        $("#sso").addClass('deactivated');

        if ($("#sso").hasClass('anonymous'))
        // It is a LOGIN action
        {
            // direct broser to SSO login page
            window.location.href = "https://sso.utu.fi/sso/XUI/#login/&goto=https%3A%2F%2Fvm.utu.fi%3A443%2Fapi%2Fsso%2flogin%3Fdestination%3D" + encodeURIComponent(window.location.pathname);
        }
        else
        // It is a LOGOUT action
        {
            // Issue Ajax query to sso/logout
            $.ajax({
                url:        '/api/sso/logout',
                type:       'GET',
                success: function(data, textStatus, xhr) {
                    // Executes only after server responds with 200
                    // Trigger 'updateState' to render the element visuals.
                    $("#sso").trigger('updateState');
                },
                complete: function(xhr, textStatus) {
                    // Executes also when server resonds with error(s)
                    console.log('/sso/logout HTTP Request status: ' + xhr.status);
                } 
            });
        }
    });


      //
/////// updateState handler function
    //
    $(_this).on('updateState', function(event) {
        // Launch an Ajax query and trigger event 'stateUpdated' (for pages).
        $.getJSON(window.location.origin + '/api/sso', function(data) {
            //console.log(".getJSON() success, role: " + data.role);
        }).done(function(data) {
            console.log(".getJSON().done(), role: " + data.role);
            // NOTE: If 'this' is used, inner HTML vanishes! (don't know why).
            $("#sso").removeClass(); // Remove all
            $("#sso").addClass(data.role);
            if (data.role == 'anonymous')
                $("#sso a").text("Login");
            else
                $("#sso a").text("Logout");
            // 'stateYodated' wvent for the page-specific code to monitor.
            // For reloading data elements, for example.
            $("#sso").trigger('stateChanged');
        })
        .fail(function(jqxhr, textStatus, error) {
            var err = textStatus + ", " + error;
            console.log(".getJSON().fail()" + err);
        })
         .always(function() {
            //console.log( ".getJSON.always()" );
         });
    });

    //
    // Element has been built, trigger event to query SSO session state and
    // render visuals accordingly.
    //
    $(_this).trigger('updateState');

    return _this;
}

// EOF
