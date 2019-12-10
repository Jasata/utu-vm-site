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
 - [Bootstrap 4.3.1](https://getbootstrap.com/docs/4.3/getting-started/introduction/)
 - [JQuery 3.4.1](https://jquery.com/download/)
 - [Font Awesome 4.7.0](https://fontawesome.com/v4.7.0/) (because that is the last free version)
 - [Datatables 1.10.20](https://datatables.net/)
 - [CardTabs 1.0](https://github.com/blekerfeld/CardTabs)
 
Backend
 - Nginx
 - Python 3.7.3 (part of Debian 10)
 - Flask & UWSGI
 - SQLite3

