# Flask Installation Notes

Raspberry Pi / Raspbian machines will be used for development (and to some extent, testing),
which is why these notes are primarily for Debian 9/10 and derived Raspbian OS'es.
Ubuntu Server specifics, if any, will be added later.

## Relevant System Directories

These directories will appear in the instructions, and are grouped here for just easy reference.

| Directory                         | Notes                                                                           |
|:----------------------------------|:--------------------------------------------------------------------------------|
| `/var/www/vm.utu.fi`              | Cloned GitHub repository.                                                       |
| `/etc/uwsgi/apps-available`       | `uwsgi` configuration file soft linked from here to `/etc/uwsgi/apps-enabled`.  |
| `/etc/nginx/sites-available`      | Nginx site configuration file location.                                         |

## Installation (Raspberry Pi)

This short guide assumes that you will be Raspberry Pi as a mini-webserver for **development** purposes.
Please note that the convention here to prefix commands with either `#` or `$` signidies the user
which is expected to run the command. `#` stands for `root` and `$` stands for `pi` for Raspberry Pi.

### Install Required Packages

    # apt install -y nginx python3-dev python3-pip python3-flask sqlite uwsgi uwsgi-plugin-python3 git

### Clone the Site

NOTE: Adding user `www-data` to group `pi` is not something you would do in a production environment!
In development usage however, it just makes things a little bit more convenient.

    # mkdir /var/www/vm.utu.fi && chown pi.pi /var/www/vm.utu.fi
    # usermod -a -G pi www-data
    $ git clone https://github.com/jasata/utu-vm-site vm.utu.fi

### Configure Nginx

`/etc/nginx/sites-available/vm.utu.fi`:
```config
    server {
        listen 80 default_server;
        listen [::]:80 default_server;

        root /var/www/vm.utu.fi;
        server_name _;

        location / {
                root /var/www/vm.utu.fi/;
                index index.html;
        }

        location /api {
            include uwsgi_params;
            uwsgi_pass unix:/run/uwsgi/vm.utu.fi.socket;
        }
    }
```

Next, remove default site linkage and link the above as enabled site:

    # cd /etc/nginx/sites-enabled
    # rm default
    # ln -s ../sites-available/vm.utu.fi

### Configure uWSGI

In Debian/Rasbian, `uwsgi` is not a `systemd` service, but is run by `init` (`/etc/init.d/uwsgi`).
Application are confgured in `/etc/uwsgi/apps-available/` files, softlinked to `etc/uwsgi/apps-enabled/`.
Application files come in various formats, but I prefer INI:

`/etc/uwsgi/apps-available/vm.utu.fi.ini`:
```ini
[uwsgi]
plugins = python3
module = application
callable = app
# Execute in directory...
chdir = /var/www/utu-vm-site/api

# Execution parameters
master = true
processes = 1
threads = 4

# Logging (cmdline logging directive overrides this, unfortunately)
logto=/var/log/uwsgi/uwsgi.log

# Credentials that will execute Flask
uid = www-data
gid = www-data

# Since these components are operating on the same computer,
# a Unix socket is preferred because it is more secure and faster.
socket = /run/uwsgi/vm.utu.fi.socket
chmod-socket = 664

# Clean up the socket when the process stops
vacuum = true

# This is needed because the Upstart init system and uWSGI have
# different ideas on what different process signals should mean.
# Setting this aligns the two system components, implementing
# the expected behavior:
die-on-term = true
```

**IMPORTANT:** `uwsgi` configuration has changed since the last time I used it:

  - .INI key-value `plugins = python3` is new and vital. `uwsgi` no longer automatically invoke Python.<br>
    Valid plugins can be listed by `ls /usr/lib/uwsgi/plugins/` ("<name>_plugin.so").
  - "To route requests to a specific plugin, the webserver needs to pass a magic number known as
    a modifier to the uWSGI instances. By default this number is set to 0, which is mapped to Python."
    [Source](https://uwsgi-docs.readthedocs.io/en/latest/ThingsToKnow.html)<br>
    In nginx configuration, this would look like: `uwsgi_modifier1 0;` within the `location { ... }`,
    but it is unnecessary because it defaults to Python (value: 0).

Or in other words, http server provides `uwsgi` with magic number that defines what service will be required
(for example, `uwsgi_modifier1 9;` would route the request to Bash script plugin), and uwsgi application
configuration files now have to tell which plugin they use (the `plugin = ` key-value).

## Restart Services and Test

    # systemctl restart uwsgi
    # systemctl restart nginx

    # curl http://localhost/hello?name=Bob

# Troubleshooting (Raspberry Pi)

  - Make sure your socket exists. That is a good indicator if the uWSGI service is up and running.
    In this setup, the socket should be in `/run/uwsgi/vm.utu.fi.socket`.
  - Query service status with `systemctl status uwsgi`.
  - Inspect logfile `/var/log/uwsgi/app/vm.utu.fi.log`.

## vm.utu.fi.log: -- unavailable modifier requested: 0 --

This "modifier" zero is the magic number that tells `uwsgi` which plugin is needed (zero = Python).
What this intends to say is; "plugin for request type 0 is not available" - or in otherwords,
you probably forgot to have `plugins = python3` in your .INI file... or you did not install the
`uwsgi-plugin-python3` package (with `apt`).

## Application not found

Another common issue is that the Flask Application is incorrectly pointed in the .INI -file.
Point your attention to keyvalues:

    module = application
    callable = app

Key `module` defines the Python file to look into (`application.py` in this case) and `callable`
defines the object which refers to an initialized `Flask` application object. Looking at our test
Flask Application file, you can see that variable `app` refers to `Flask` application object:

```python
import syslog
from flask import Flask, escape, request

syslog.syslog("Flask Test Application invoked!")
app = Flask(__name__)

@app.route('/hello')
def hello():
    name = request.args.get("name", "World")
    return f'Hello, {escape(name)}!'

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return f"You want path: '{path}'"

if __name__ == "__main__":
    app.run()

```
