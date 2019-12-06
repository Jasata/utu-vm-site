# University of Turku - Course Virtualization

Simple set of pages for university's course virtualization project.

### Design Goals

 - **Simplicity** (in implementation, site structure, usage...).
 - Minimal dependencies (see "Third-party components").
 - Small scope (Only the essentials are "opened up" on asite. More detailed information will be provided by linking to GitLab/PDF documents).
 - **Two-step principle**. All actions (primary use cases) should be accomplished in no more than two clicks. One to choose the relevant subpage, another to open a folding information container (if necessary).
 
Primary use cases (in order of importance)
 1. Student retrieves course-specific virtual machine image
 2. Student comes to learn how to set his or her personal system up to run virtual images
 3. Student comes to resolve an issue and/or report it
 4. Lecturer uploads a new course-specifc virtual machine
 5. Lecturer comes to learn about this tool and its benefits
 6. Lecturer seeks technical documentation on how to create new virtual images
 7. Lecturer comes to seek assistance / help


## Server

Original idea about separate virtual server has been dropped in favor of expanding ftdev resources and reserving an additional DNS name for it (https://vm.utu.fi).

## Functional Specifications

 - Publishes a download list (in the downloads -page) of available .OVA files.
 - OVA metadata will be a combination of extracted XML from OVA and uploader specified information.
 - Download statistics will be based on webserver log files, which will be generated into (some kind of) graph/report nightly and made available in separate statistics page.

### Items That Need Technical Solutions
 - Authentication (without actual identification). Perhaps Kerberos module relying on UTU authentication.
 - Integration of distribution builder - as a separate Build Manager agent, providing a REST API interface.
- Will the REST API to Build Manager be routed via nginx for Kerberos authentication?

## Third-party components

Frontend
 - Bootstrap 4.3.1
 - JQuery 3.4.1
 - Awesome Fonts 4.7.0
 
Backend
 - nginx
 - Python 3.7.x (part of Debian 10)
 - Flask & UWSGI
 - SQLite3

## Installation (Raspberry Pi)

Initial backend development will take place in Raspberry Pi and once suitable releasable version is ready, ftdev installation is undertaken.

This short guide assumes that you will be installing the site code into a mini-webserver for development purposes. In that case, it is a convenience to have the files located in your home directory.

**NOTE: Untested (to be verified)**

Install required packages

    # apt install -y nginx python3-dev python3-pip python3-flask sqlite uwsgi uwsgi-plugin-python3 git

Clone the site and add `www-data` to group `pi` (note: user executes the third command):

    # mkdir /var/www/utu-vm-site && chown pi.pi /var/www/utu-vm-site
    # usermod -a -G pi www-data
    $ ssh-keygen -t rsa

Enter `~/.ssh/id_rsa.pub` into your GitHub account before you proceed in cloning (gives permission denied otherwise).

    $ git clone git@github.com:Jasata/utu-vm-site.git /var/www/utu-vm-site

However, these might work without GitHub account (to-be-tested):

    $ git clone git://github.com/jasata/utu-vm-site.git
    $ git clone https://github.com/jasata/utu-vm-site

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

**Rasbian/Debian uwsgi**

[Source](https://www.linode.com/docs/web-servers/nginx/use-uwsgi-to-deploy-python-apps-with-nginx-on-ubuntu-12-04/)

`uwsgi` is not a `systemd` service, but is run by `init` (`/etc/init.d/uwsgi`). Application are confgured in `/etc/uwsgi/apps-available/` files, softlinked to `etc/uwsgi/apps-enabled/`. Application files are in XML:

`/etc/uwsgi/apps-available/utu-vm-site.xml`:
```xml
<uwsgi>
    <plugin>python</plugin>
    <socket>/run/uwsgi/app/utu-vm-site/utu-vm-site.socket</socket>
    <pythonpath>/srv/www/utu-vm-site/</pythonpath>
    <app mountpoint="/">

        <script>wsgi_configuration_module</script>

    </app>
    <master/>
    <processes>4</processes>
    <harakiri>60</harakiri>
    <reload-mercy>8</reload-mercy>
    <cpu-affinity>1</cpu-affinity>
    <stats>/tmp/stats.socket</stats>
    <max-requests>2000</max-requests>
    <limit-as>512</limit-as>
    <reload-on-as>256</reload-on-as>
    <reload-on-rss>192</reload-on-rss>
    <no-orphans/>
    <vacuum/>
</uwsgi>
```

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
  - WinSCP (VSC drag'n-drop works only towards remote!)

