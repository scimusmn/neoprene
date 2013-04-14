# Fabric modules
from fabric.api import (cd, env, hide, run, settings, task)
from fabric.contrib.files import (exists)
from fabric.contrib.console import (confirm)
from fabric.colors import blue, red, green

# Neoprene modules
import cache
import db
import files

# Velour modules
import velour as git

# Python modules
from contextlib import contextmanager
import re


# Source your local environment variables to make Drush work properly
env.shell = "/bin/bash -l -c -i"


@contextmanager
def _mute():
    """Run a fabric command without reporting any responses to the user. """
    with settings(warn_only='true'):
        with hide('running', 'stdout', 'stderr', 'warnings'):
            yield


def _header(txt):
    """Decorate a string to make it stand out as a header. """
    wrapper = "------------------------------------------------------"
    return blue(wrapper + "\n" + txt + "\n" + wrapper, bold=True)


def _cleanup_drush_output(o):
    """Cleanup drush output to get raw message string.

    This is useful when you need to run a regex against a response string
    and don't want to deal with any of the special formatting and linebreaks
    that Drush can return

    Args:
        o: Drush output string

    Returns:
        Raw response string
    """
    # Remove linebreaks
    r = ' '.join(o.splitlines())
    # Remove Drush decoration which can show up anywhere in the message
    r = re.sub('\[success\]', '', r)
    # Remove extraneous white space
    r = re.sub('\s+', ' ', r)
    return r


def confirm_overwrite(warning):
    """Prompt the user with a noticable warning before overwriting files

    Args:
        warning: Warning string to be presented to the user. This should
            include the question string, but not the [y/N] bit. That's
            added by Fabric's confirm function. Defaults to No.

    Returns:
        Quits all operations if the user says No.
        Continues operations with a pass if the user says Yes.
    """
    answer = confirm(red(warning), default=False)
    if answer is not True:
        exit('Quiting')
    else:
        pass


@task
def site_install(path, db_user, db_pass, db_host, db_name):
    """Install a fresh Drupal site

    Use Drush to setup the Drupal structure in database

    Args:
        path: Directory of the website
        db_user: Database user to use when creating and running the Drupal site
        db_pass: That user's password
        db_host: Database host
        db_name: Database name
    """
    db_url = 'mysql://%s:%s@%s/%s' % (db_user, db_pass, db_host, db_name)
    warning = """
WARNING: This is an inherently insecure method for interacting with the
database since the database password will be written to the command line
and will be visible to anyone who can access the .mysql_history. Additionally,
while this command is being run the password is exposed to anyone who can run
the ps command on the server. Unfortunately this is the only method that
Drush currently supports.

Do you still wish to proceed?
"""
    confirm_overwrite(warning)

    with cd(path):
        run("drush site-install standard --db-url=" + db_url)


@task
def download(parent, name=None):
    """Download the latest Drupal project

    Args:
        parent: Parent directory where the site will be created
        name: Directory name for the site. Defaults to the Drupal project name
            (default None)

    Usage:
        $ fab -H example.com download:'/path/to/web/dir','vanilla'

        Will download the latest Drupal project to /path/to/web/dir/vanilla
    """
    with cd(parent):
        if not name:
            run("drush dl")
        else:
            run("drush dl --drupal-project-rename=%s" % name)


@task
def dev_site(live_path, dev_parent='', dev_name='', dev_db_name='',
             base_url='', rewrite_base=''):
    """Create a dev site by copying an existing live site

    Args:
        live_path: The path to the operational live site
        dev_parent: Parent directory where the dev site will be created
        dev_name: Directory name for the dev site
        dev_db_name: Name of the database that will be created for the dev site
        base_url: Base URL value to write in the dev settings.php file.
            If left blank, this value will remain commented out in settings.php
            ( default=None )
        rewrite_base: RewriteBase value to write in the dev .htaccess file.
            If left blank, this value will remain commented out in .htaccess
            ( default=None )

    Usage:
        $ fab -H example.com dev_site:'/path/to/live/site',\
        > '/path/to/dev/parent','develop','drupal_dev_01',\
        > 'http://dev.example.com/develop','/develop'
    """
    # cd to the live site
    remote = git.get_remote(live_path)

    with cd(dev_parent):
        run('git clone %s %s' % (remote, dev_name))

    # Look for an git origin in the live site

    # cd to the dev parent dir and clone the repo from origin

    # switch to the develop branch

    # git fetch

    # git pull origin develop

    # Duplicate the live mysql db as a dev db
    # Look into cross platform ways to just do the db duplication without
    # needing to write the db dump file and then do the insert

    # Configure the settings.php and .htaccess files for the dev site

    # Copy the files folder from the live site to the dev site
    # Eventually there should be a option here for doing read only sym-links
    # Or maybe some S3 thingy

    # drush cc all on dev

    # done


@task
def vanilla_site(parent, name, db_name, base_url=None, rewrite_base=None):
    """Setup a complete, vanilla Drupal install

    Download Drupal, configure the settings.php database file, configure
    the .htaccess file, and then populate the database with the default
    Drupal structure.

    Args:
        parent: Parent directory where the site will be created
        name: Directory name for the site
        db_name: Name of the database that will be created for this site
        base_url: Base URL value to write in the settings.php file.
            If left blank, this value will remain commented out in settings.php
            ( default=None )
        rewrite_base: RewriteBase value to write in the .htaccess file.
            If left blank, this value will remain commented out in .htaccess
            ( default=None )

    Usage:
        $ fab -H 127.0.0.1 vanilla_site:'/path/to/web/dir','vanilla','drupal_vanilla'

        Will create a site at /path/to/web/dir/vanilla on your local machine.
        It will create a database called drupal_vanilla, populating with with
        the base Drupal tables.

        $ fab -H example.com vanilla_site:'/var/www/html,'special','drupal_dev_01','http://www.example.com/special','/special'

        Will create a site at http://example.com/special with the appropriate
        Apache config options to make it work in a sub-directory. Results
        will depend on your Apache configuration.
    """

    # TODO check for trailing slash
    path = parent + '/' + name

    print _header("Checking dependencies")
    if exists(path):
        warning = """
A folder already exists at your destination path.

Do you wish to overwrite?
"""
        confirm_overwrite(warning)
        run("chmod -R u+w %s" % path)
        run("rm -rf %s" % path)

    if db.mysql_cnf_password_set():
        password = db.get_mysql_pass()
        print
        print green("You're ready to build a Drupal site.")
        print
    else:
        exit('No MySQL credentials were found. Quitting.')

    print _header("Downloading Drupal.")
    download(parent, name)

    print _header("Configuring the RewriteBase in the .htaccess file.")
    files.enable_rewrite_base(path, rewrite_base)

    print _header("Making the files directory and a settings.php file")
    files.setup_files(path)
    files.setup_settings(path, db_name)

    print _header("Creating the database and loading Drupal structure.")
    site_install(path, 'bkennedy', password, '127.0.0.1', db_name)

    with cd(path):
        cache.clear()

    print _header("Your Drupal site is ready to go.")

    # run("drush dl -y devel backup_migrate")
    # Send an email as part of the Jenkins build or at least print the URL
