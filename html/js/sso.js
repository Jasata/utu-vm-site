/*
 * sso.js - Jani Tammi <jasata@utu.fi>
 *
 *  2019-12-22  Initial version.
 *  2019-12-22  State and visuals now one and the same
 *  2019-12-22  Remove ::after and compact design
 *  2019-12-23  CANNOT USE Flask session! REST API model implemented
 *  2019-12-23  Domain-SSO redirect added
 *  2019-12-23  Clean out unnecessary debug messages
 *  2019-12-25  Add 'stateChanged' event for pages
 *  2020-01-01  API endpoints now under /api/sso
 *  2020-08-30  Enhance code comments
 *  2020-08-30  Domain-SSO redirect now preserves URL parameters
 *  2020-09-04  'stateChanged' event triggers with role data
 *  2020-09-12  Fixed hardcoded SSO goto URL into window.location.hostname
 *
 *
 *  As the last action, the element build (.sso() -function) triggers an
 *  'ssoUpdateState' event which causes the element to issue an Ajax query,
 *  change the class of the element accordingly and finally trigger
 *  'stateChanged' event with the role string as an additional argument.
 *
 *  THIS MEANS THAT THE CLASS / LOGIN STATE IS **NOT** AVAILABLE IMMEDIATELY
 *  IN THE $(document).ready() FUNCTION!!!
 *
 *  PROPER WAY TO CONDITIONALLY RENDER CONTENT
 * ============================================================================
 *  CSS Classes record login status: ['anonymous', 'student', 'teacher'].
 *  It may temporarily have a class 'deactivated', but only for duration of
 *  an Ajax query (to reject user input until complete).
 *
 *  Write an event handler for 'stateChanged' event, create it in the
 *  $(document).ready() -function:
 *
 *      // Document ready - initialize page elements
 *      $(document).ready(function() {
 *          // Initialize SSO element
 *          $('#sso').sso();
 *          // SSO stateChanged event handler
 *          $("#sso").on("stateChanged", function(event, role) {
 *              if (role === 'teacher') {
 *                  console.log("TODO: Render page content");
 *              } else {
 *                  console.log("Access Denied!");
 *              }
 *          });
 *      });
 *
 *
 *  HOW TO USE
 * ============================================================================
 *
 *  Include CSS and Javascript files in your HTML:
 *
 *      <link rel="stylesheet" href="css/sso.css">
 *      <script src="js/sso.js"></script>
 *
 *  Add somewhere a Login/Logout element (must have ID="sso"):
 *
 *      <div id="sso"></div>
 *
 *  Build the SSO Login/Logout element after page has loaded:
 *
 *      <script>
 *          $(document).ready(function() {
 *              $("#sso").sso();
 *              $("#sso").on("stateChanged", function(event, role) {
 *                  if (role === 'teacher')
 *                      console.log('You are a teacher!');
 *              });
 *          });
 *      </script>
 *
 *  NOTE: Obviously, a server side endpoints are also required...
 * 
 *
 *  FOR LOGOUT / LOGIN
 *  ===========================================================================
 *  #sso emits a 'stateChanged' event on login/logout for pages to handle.
 *  All dynamic elements in the page must support at least:
 *
 *      - Disabled or "empty" state (for unauthorised session)
 *      - Load, Reload amd Empty content
 *
 *  SSO INTERNAL STATES
 *  ===========================================================================
 *  Internally, '#sso' element can have 1 of 4 states
 *
 *  deactivated
 *          Transient state during which the element does not accept input.
 *          Set when the module starts login or logout sequence and replaced
 *          with the new role [anonymous | student | teacher] -state (class).
 *  anonymous
 *          Unauthenticated user. Either has not yet logged in or cannot login
 *          because has no account.
 *  student
 *          UTU SSO Session is authenticated / valid, but the UID is not listed
 *          in the database - thus the user is a student.
 *  teacher
 *          Authenticated UTU SSO session AND the UID is found in the database.
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
            // Use current hostname, not hardcoded...
            window.location.href = `https://sso.utu.fi/sso/XUI/#login/&goto=https%3A%2F%2F${window.location.hostname}%3A443%2Fapi%2Fsso%2flogin%3Fdestination%3D`
            // window.location.href = "https://sso.utu.fi/sso/XUI/#login/&goto=https%3A%2F%2Fvm.utu.fi%3A443%2Fapi%2Fsso%2flogin%3Fdestination%3D" + encodeURIComponent(window.location.pathname + window.location.search);
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
                    $("#sso").trigger('ssoUpdateState');
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
    $(_this).on('ssoUpdateState', function(event) {
        // Launch an Ajax query and trigger event 'stateUpdated' (for pages).
        $.getJSON(window.location.origin + '/api/sso', function(data) {
            //console.log(".getJSON() success, role: " + data.role);
        }).done(function(data) {
            //console.log(".getJSON().done(), role: " + data.role);
            // NOTE: If 'this' is used, inner HTML vanishes! (don't know why).
            $("#sso").removeClass(); // Remove all
            $("#sso").addClass(data.role);
            if (data.role == 'anonymous')
                $("#sso a").text("Login");
            else
                $("#sso a").text("Logout");
            // Emit 'stateUpdated' event for the page code to react on
            // role change (reloading data elements, for example).
            $("#sso").trigger('stateChanged', data.role);
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
    $(_this).trigger('ssoUpdateState');

    return _this;
}

// EOF
