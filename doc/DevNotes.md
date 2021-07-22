# Developer Notes

_This file exists for the sole purpose that I revisit this project so seldomly that I simply cannot remember all related commands or details every time. Thus, I am doing myself a service and writing some of this stuff down (and appending this as time goes...)._

## Local Development Instance

 - Masqueraded via `tunkki.home.net` as `vm.utu.fi`, at the time of writing Raspberry#31 (top shelf).
 - User `pi` must be added to group `www-data` (`# usermod -a -G pi www-data`).
 - User `pi` must own the www root (`chown pi.pi /var/www/vm.utu.fi`).
 - This project has installer which configures the instance. _Remember to run it, if new dev instance is created!_
 - VSC Remote-SSH may time-out on initial connections. It has always been like that - just reconnect.

Development instance packages:
```
# apt install -y nginx python3-dev python3-pip python3-flask sqlite uwsgi uwsgi-plugin-python3 git
```
### HTTPD Service Configuration

`/etc/nginx/sites-available/wm.utu.fi`:
```
    server {
        listen 80 default_server;
        listen [::]:80 default_server;

        root /var/www/vm.utu.fi;
        server_name _;

        location / {
            include uwsgi_params;
            uwsgi_pass unix:/run/uwsgi/vm.utu.fi.socket;
        }
    }
```
```
# ln -s /etc/nginx/sites-available/vm.utu.fi /etc/nginx/sites-enabled/vm.utu.fi
# systemctrl restart nginx
```

`/etc/uwsgi/apps-available/wm.utu.fi.ini`:
```
[uwsgi]
plugins = python3
module = application
callable = app
# Execute in directory...
chdir = /var/www/vm.utu.fi/

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

```
# ln -s /etc/uwsgi/apps-available/wm.utu.fi.ini /etc/uwsgi/apps-enabled/wm.utu.fi.ini
# systemctrl restart uwsgi.service
```

__Instance Configuration / Setup__

__TODO:__ `/var/www/vm.utu.fi/setup.py` script ...has not been written (thought I did...). When written, it needs to address:
 - `instance/application.conf`
 - Numerous JavaScript files have items that need to be set on configuration time. Find a way to give them a common configuration file.


## Logs

 - `/var/log/nginx/access.log`
 - `/var/log/uwsgi/app/vm.utu.fi.log`
 - ´/var/www/vm.utu.fi/application.log`

