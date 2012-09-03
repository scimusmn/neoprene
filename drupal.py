from fabric.api import (abort, cd, env, hide, get, local, prompt, run,
                        settings, task)
from contextlib import contextmanager
import re

# Degug code for development.
# This should eventually come out.
#from pprint import pprint


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
    with _mute():
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
        with _mute():
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


def db_create(place, db_name, db_host, db_user, db_pass):
    """
    Try to create a database.

    We'll be conservative here and just let the task fail if a database
    already exists with the same name.
    """
    create = 'mysqladmin create %s -h %s -u %s' % (db_name, db_host, db_user)
    if db_pass is not None:
        create = create + " -p %s" % db_pass
    if place == 'remote':
        pass
        #o = run(create)
    if place == 'local':
        with _mute():
            db_response = local(create, True)
    return db_response


def interactive_create_db(place, db_host, db_user, db_pass):
    """
    Keep asking the user for a database name until the
    db_create function stops returning errors.
    """
    error_code = 1
    while error_code == 1:
        # Ask the user for a clean database
        txt = "What would you like to call you local database?"
        print
        db_name = prompt(txt)
        db_response = db_create(place, db_name, db_host, db_user,
                                db_pass)
        if db_response.return_code == 1:
            print db_response.stderr
            print
            print "Try again...or CTRL-C to exit."
        else:
            error_code = db_response.return_code
    return db_name


@task
def pull_db(directory, local_db_host='localhost', local_db_user=None,
            local_db_pass=None):
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

    if local_db_user is None:
        with _mute():
            local_db_user = local('whoami', True)

    print "Writing to your local database using these credentials:"
    print "  hostname: %s" % local_db_host
    print "  username: %s" % local_db_user
    if local_db_pass is None:
        print "  password: defined in ~/.my.conf"
    else:
        print "  password: ***"

    # Try to create a database
    interactive_create_db('local', local_db_host, local_db_user, local_db_pass)

    # Find the name of the local sql file
    # local_db_import(sql_file)


@task
def cache_clear():
    """ Clear the database cache on a Drupal website """
    run("drush cache-clear")
