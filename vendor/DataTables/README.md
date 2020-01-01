# DataTables

Spamiel from [DataTables website](https://datatables.net/)

*DataTables is a plug-in for the jQuery Javascript library. It is a highly flexible tool, built upon the foundations of progressive enhancement, that adds all of these advanced features to any HTML table.*

## DataTables in this Application

DataTables offers a compile/compose and download service at their [website](https://datatables.net/download/) that lets users download only the relevant parts for their application.

This application has selected the following options:

| Option                         |  Version        | Use                                     |
|:-------------------------------|:----------------|:----------------------------------------|
| Styling Framework: DataTables  | v1.10.20        | Styling                                 |
| DataTables (core)              | v1.10.20        | Core libraries                          |
| Extension: Responsive          | v2.2.3          | Enables responsive behavior             |
| Extension: Select              | v1.3.1          | Adds selection abilities to a table     |

Download option **Minify** and **Concatenate** are both selected.

* **Responsive** is obviously desired feature in all uses, and needs no explanation.
* **Select** is for "Upload and Manage" UI, where DataTables are used as a selection control to populate the actual editing form.

**NOTE:** The Bootstrap styling framework was not opted, because removing Boostrap completely was considered a viable option. Due to time constraints, Bootstrap has not been removed (by 01.01.2020).

## Installation directory

The **concatenate** option ensures that all extensions are included in the two included files; `datatables.css` and `datatables.js`. They are linked normally from the `vendor` directory to the `html/css` and `html/js` directories.

