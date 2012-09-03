from fabric.api import (abort, cd, env, hide, get, local, prompt, run,
                        settings, task)
from contextlib import contextmanager
import re

# Degug code for development.
# This should eventually come out.
from pprint import pprint


def _header(txt):
    wrapper = "------------------------------------------------------"
    return wrapper + "\n" + txt + "\n" + wrapper


@contextmanager
def _mute():
    """
    Run a fabric command without reporting any responses to the user.
    """
    with settings(warn_only='true'):
        with hide('running', 'stdout', 'stderr', 'warnings'):
            yield


def _which_download_app():
    """
    Find the path to a download application, prefering wget.
    Abort if neither is found.
    """
    with settings(warn_only=True):
        with hide('running', 'stdout', 'stderr', 'warnings'):
            path = local("which wget", True)
            if path.return_code != 1:
                return path
            else:
                path = local("which curl", True)
                if path.return_code != 1:
                    return path + " -O"
                else:
                    abort("Please install wget or curl on your local system.")


def _cleanup_drush_output(o):
    """
    Cleanup drush output to get raw message string.
    """
    # Remove linebreaks
    r = ' '.join(o.splitlines())
    # Remove Drush decoration which can showup anywhere in the message
    r = re.sub('\[success\]', '', r)
    # Remove extraneous white space
    r = re.sub('\s+', ' ', r)
    return r


@task
def remote_db_dump(directory):
    """
    Uses Drush and the Backup and Migrate module to make a SQL dump of the
    database for the spcified site.

    Returns the full filepath to the backup

    Usage:
        fab -H deployuser@example.com remote_db_dump:'/site/path/'
    """
    with cd(directory):
        o = run("drush bam-backup")
        r = _cleanup_drush_output(o)
        # Get the backup filename from the response
        r = re.match('Default Database backed up successfully to ([^\s]*) '
                     'in destination Manual Backups Directory in '
                     '[\d]*\.[\d]* ms.',
                     r
                    )
        bam_filename = r.group(1) + ".mysql.gz"

        # No need to show this to the users
        with settings(warn_only=True):
            with hide('running', 'stdout', 'stderr', 'warnings'):
                file_private_path = run("drush vget file_private_path")
                # Remove quotes around the variable
                r = re.match('file_private_path: "([^"]*)"', file_private_path)
                bam_path = r.group(1) + "/backup_migrate/manual/"

        with cd(bam_path):
            bam_filepath = env.cwd + bam_filename
            return bam_filepath


@task
def local_db_import(sql_file):
    """
    Import a SQL file into a local database
    """
    local("mysql database_name < sql_file.sql")


def db_create(place, db_name):
    """
    Try to create a database.

    We'll be conservative here and just let the task fail if a database
    already exists with the same name.
    """
    create = 'mysqladmin create %s' % (db_name)
    if place == 'remote':
        o = run(create)
    if place == 'local':
        with settings(warn_only=True):
            o = local(create, True)
            #return_code, stderr, failed and succeeded
            print "--return_code--"
            pprint(o.return_code)
            print "--stderr--"
            pprint(o.stderr)
            print "--failed--"
            pprint(o.failed)
            print "--succeded--"
            pprint(o.succeded)


@task
def pull_db(directory):
    """
    Get a copy of a remote website's db on your local machine.

    Usage:
        fab -H deployuser@example.com pull_db:'/path/to/drupal/site/root'
    """
    txt = "Getting a database backup of your remote site."
    print
    print _header(txt)
    print

    path = remote_db_dump(directory)
    localpath = get(path, "~/")
    local("gunzip %s" % localpath[0])

    txt = "Importing the database on your local machine."
    print
    print _header(txt)

    print """
Since you didn't define local database credentials
I'm assuming some MySQL defaults:
"""
    with _mute():
        mysql_u = local('whoami', True)
    print "username: %s" % mysql_u
    print "password: defined in ~/.my.conf"
    print "host: localhost"

    #, I'm using your
#current system username to access MySQL. I'm also assuming
#that the password is defined in ~/.my.conf.

#Define the MySQL credential arguments to override this behavior.
#"""

    # Ask the user for a clean database
    txt = "What would you like to call you local database?"
    local_database = prompt(txt)

    # Check that the database is clean
    db_create('local', local_database)

    # Find the name of the local sql file
    # local_db_import(sql_file)


@task
def cache_clear():
    """ Clear the database cache on a Drupal website """
    run("drush cache-clear")
