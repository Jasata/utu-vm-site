# University of Turku - Course Virtualization

Simple set of pages for university's course virtualization project.

### Design Goals

 - **Simplicity** (in implementation, site structure, usage...).
 - Minimal dependencies (see "Third-party components").
 - Small scope (Only the essentials are "opened up" on asite. More detailed information will be provided by linking to GitLab/PDF documents).
 - **Two-step principle**. All actions (primary use cases) should be accomplished in no more than two clicks.
 
Primary use cases (in order of importance)
 1. Student retrieves course-specific virtual machine image
 2. Student comes to learn how to set his or her personal system up to run virtual images
 3. Student comes to resolve and issue and/or report it
 4. Lecturer uploads a new course-specifc virtual machine
 5. Lecturer comes to learn about this tool and its benefits
 6. Lecturer seeks technical documentation on how to create new virtual images
 7. Lecturer comes to seek assistance / help

### Release Schedule

Non-binding target to have release candidate 1 ready by the end of November 2019.

## Server Requirements

### Virtual server instance from UTU-Shop

 - **Usage:** Opetusvälineet
 - **Domain:** https://vm.utu.fi
 - **Server name:**
 - **SSL:** YES
 - **Operating system:** Ubuntu server LTS
 - **Prod/Test/Dev:** Tuotanto
 - **Port openings:** HTTPS
 - **Backup level:** 2 viikkoa
 - **Admin account:** jasata
 - **Other admins:** jmjmak; samnuutt
 - **Additional information:** Install flask/uwsgi and python 3.7+

## Functional Specifications

 - Publishes a download list (in the downloads -page) of .OVA files located in Gitlab repository.
 - List to be published and additional information encoded in publish-in-vm.utu.fi.md (subject to change). This file is periodically retrieved and automatically parsed to regenerate the download list.
 - Download links point to vm.utu.fi for click counting and redirection.

 - Generates statistics daily and publises it in a separate page.

 - If feasible, sources documentationfor students from Gitlab. However, simplicity and readability takes precedence over automation. This is for students and primary goal is to serve them, not us.
 - Documentation for lecturers is redirected to Gitlab wiki.

## Third-party components

Frontend
 - Bootstrap 4.3.1
 - JQuery 3.4.1
 - (CDN) Awesome Fonts 4
 
Backend
 - nginx
 - Python 3.7.x (part of Debian10)
 - Flask & UWSGI
 - SQLite3

## Installation

This short guide assumes that you will be installing the site code into a mini-webserver for development purposes. In that case, it is a convenience to have the files located in your home directory.

**NOTE: Untested (to be verified)**

Install required packages

    # apt install -y nginx python3-dev python3-pip python3-flask sqlite uwsgi uwsgi-plugin-python3

Clone the site and add `www-data` to group `pi` (note: user executes the third command):

    # mkdir /var/www/utu-vm-site && chown pi.pi /var/www/utu-vm-site
    # usermod -a -G pi www-data
    $ git clone git@github.com:Jasata/utu-vm-site.git /var/www/utu-vm-site

Replace `/etc/nginx/sites-available/default` with:

    server {
        listen 80 default_server;
        listen [::]:80 default_server;

        root /var/www/utu-vm-site;
        server_name _;
        location / {
            include uwsgi_params;
            uwsgi_pass unix:/tmp/nginx.uwsgi.sock;
        }
    }

Configure Flask, write `/etc/uwsgi`:

    [uwsgi]
    module = application:app
    # Execute in directory...
    chdir = /var/www/utu-vm-site
    master = true
    processes = 1
    threads = 2

    # Credentials that will execute Flask
    uid = www-data
    gid = www-data

    # Since these components are operating on the same computer,
    # a Unix socket is preferred because it is more secure and faster.
    socket = /tmp/nginx.uwsgi.sock
    chmod-socket = 664

    # Clean up the socket when the process stops
    vacuum = true

    # This is needed because the Upstart init system and uWSGI have
    # different ideas on what different process signals should mean.
    # Setting this aligns the two system components, implementing
    # the expected behavior:
    die-on-term = true

Cloning brought the application config file, and now we can reload Nginx:

    # systemctl restart nginx

**http://localhost should now serve the site index.**

# vm.utu.fi - Site for Virtual Courses

## Development environment for Tuisku

TIERS Equipement to borrow
  - Raspberry Pi 3 B+
  - SanDisk Ultra 16GB A1 class uSD
  - 220V PSU / 5 V, 3A wallwart
  - USB Type-A to microUSB power cable 40 cm
  - RJ45 Ether cable 1m
  
 System creation
  - 2019-09-26-raspbian-buster-lite.img
  - `apt update && apt upgrade`
  - `apt install git nginx python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools`
  - Configure `/etc/nginx/sites-available/default` to point to `/home/pi/utu-vm-site` (with uwsgi)
  - Configure UWSGI
  - Enable service (may not be necessary anymore with modern UWSGI package - FIND OUT!)
  - **change to local user `pi`**
  - Add workstation (Windows) public SSH key to `~/.ssh/authorized_keys`
  - Congifure Git `git config --global user.name "NAME NAME"` and `git config --global user.email "email@utu.fi"`
  - `cd && git clone git@github.com:Jasata/utu-vm-site.git` (creates the `/home/pi/utu-vm-site`)

Tools for workstation
  - Visual Studio Code with Remote - SSH extension
  - WinSCP (or does drag-n-drop via Visual Studio Code now work?)

