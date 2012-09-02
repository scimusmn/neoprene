from fabric.api import *
from fabric.contrib.console import confirm

import re

# Degug code for development.
# This should eventually come out.
from pprint import pprint

def _header(txt):
    wrapper = "------------------------------------------------------"
    return wrapper + "\n" + txt + "\n" + wrapper

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
        fab -H deployuser@example.com remote_db_dump:'/path/to/drupal/site/root'
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
    localpath = get(path,"~/")
    local("gunzip %s" % localpath[0])

    txt = "Importing the database on your local machine."
    print
    print _header(txt)
    print

    txt = "What would you like to call you local database?"
    local_database = prompt(txt)

    pprint(local_database)

    local_db_import(local_database)
    # Ask the user for a clean database
    # Check that the database is clean
    # import_db_local(sql_file)

@task
def clear_cache():
    """ Clear the database cache on a Drupal website """
    run("drush cache-clear")
