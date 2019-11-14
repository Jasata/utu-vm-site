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
 - Python 3.7.x
 - Flask & UWSGI

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
  
