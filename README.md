# University of Turku - Course Virtualization

Simple set of pages for university's course virtualization project.<br />
View static version of this project at [github.io](https://jasata.github.io/utu-vm-site/html/).

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

See [Flask document](Flask.md) for details.

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

