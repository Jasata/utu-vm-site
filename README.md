# University of Turku - Course Virtualization

A website for university's Course Virtualization project. Serves both students (get hypervisor installed and download course specific virtual machine images) and teachers (learn how virtual machines could help running a course, instructions on how to create an virtual machine image, how to get help doing it, uloading and publishing made images).

**See also:**

  * [Static version](https://jasata.github.io/utu-vm-site/html/) of this project at github.io.
  * [Wiki pages](https://github.com/Jasata/utu-vm-site/wiki) for technical and design notes.

## Design Goals

 - **Simplicity** (in implementation, site structure, usage...).
 - Minimal dependencies (see "Third-party components").
 - Small scope (Only the essentials discussed in the site. More detailed information will be provided in form of PDF documents).
 - **Two-step principle**. All actions (primary use cases) should be accomplished in no more than two clicks. One to choose the relevant subpage, another to open a folding information container (if necessary).
 
### Primary use cases (in order of importance)
 1. Student retrieves course-specific virtual machine image
 2. Student comes to learn how to set his or her personal system up to run virtual images
 3. Student comes to resolve an issue and/or report it
 4. Lecturer uploads a new course-specifc virtual machine
 5. Lecturer comes to learn about this tool and its benefits
 6. Lecturer seeks technical documentation on how to create new virtual images
 7. Lecturer comes to seek assistance / help


## Server

Original idea about separate virtual server has been dropped in favor of expanding ftdev resources and reserving an additional DNS name for it (https://vm.utu.fi). Or in other words, vm.utu.fi is a *virtual host* in ftdev.utu.fi (virtual server).

## Functional Specifications

 - Publishes a download list (in the downloads -page) of available .OVA files.
 - OVA metadata will be a combination of extracted XML from OVA and uploader specified information.
 - Download statistics will be based on webserver log files, which will be generated into (some kind of) graph/report nightly and made available in separate statistics page.
 - Uses UTU SSO authentication, but restricts itself to UTU UID only. No other **P**ersonally **I**dentifiable **I**nformation (PII) is handled or stored. (NOTE: Students have **no** PII of any kind stored).

## GDPR

*IT-Services will be consulted about UID as PII data. If UID alone is also considered to enough to bring this solution under GDPR regulations, solution model where all UID's are one-way hashed (both in client's session storage and `teacher` database table) will be proposed.*

2020-01-10 update: In a meeting, it has been said that storage of UTU SSO UID (for teachers) is allowable as long as this is clearly indicated in the data privacy statement, along with the description of its usage, purpose for storing it, expected lifetime (when and/or under what conditions it will be cleaned out) and providing a way to exercice all the rights granted by GDPR (which in our case, is a communique to support email address).

### Items That Need Technical Solutions

 - Integration of distribution builder - as a separate Build Manager agent, providing a REST API interface.
 - HTML5 File API based Flow.js needs server side implementation in Python, since nothing even remotely acceptable exists.

## Third-party components

Frontend
 - [Bootstrap 4.3.1](https://getbootstrap.com/docs/4.3/getting-started/introduction/)
 - [JQuery 3.4.1](https://jquery.com/download/)
 - [Font Awesome 4.7.0](https://fontawesome.com/v4.7.0/) (because that is the last free version)
 - [Datatables 1.10.20](https://datatables.net/) for download page tables
 - [CardTabs 1.0](https://github.com/blekerfeld/CardTabs) for tabulated content
 - [Flow.js v.2.13.2](https://github.com/flowjs/flow.js/) for HTML5 File API transfers
 
Backend
 - Nginx
 - Python 3.7.3 (part of Debian 10)
 - Flask & UWSGI
 - SQLite3

