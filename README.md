# University of Turku - Course Virtualization

Simple set of pages for university's course virtualization project.

### Design Goals

 - **Simplicity** (in implementation, site structure, usage...)
 - Minimal dependencies (see "Third-party components")
 - tba

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
 - **Additional information:** Install flask and python 3

## Functional Specifications

 - Publishes a download list (in the downloads -page) of .OVA files located in Gitlab repository.
 - List to be published and additional information encoded in publish-in-vm.utu.fi.md (subject to change). This file is periodically retrieved and automatically parsed to regenerate the download list.
 - Download links point to vm.utu.fi for click counting and redirection.

 - Generates statistics daily and publises it in a separate page.

 - If feasible, sources documentationfor students from Gitlab. However, simplicity and readability takes precedence over automation. This is for students and primary goal is to serve them, not us.
 - Documentation for lecturers is redirected to Gitlab wiki.

## Third-party components

 - Bootstrap 4.3.1
 - JQuery 3.4.1
 - (CDN) Awesome Fonts 4
 
