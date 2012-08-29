from fabric.api import *
from fabric.contrib.console import confirm

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
        # Get the backup filename from the response
        r = re.match('Default Database backed up successfully to '
                      '([^\s]*) '
                      'in destination Manual Backups Directory in '
                      '[\d]*\.[\d]* ms\.[\s]*\[success\]',
                      o
                    )
        file = r.group(1) + ".mysql.gz"
        o = run("drush vget file_private_path")
        r = re.match('file_private_path: "([^"]*)"', o)
        path = r.group(1) + "/backup_migrate/manual/"
        filepath = directory + path + file
        return filepath

@task
def get_db_dump(directory):
    """
    Download a db dump from the Backup and Migrate folder on a website.
    """
    app = _which_download_app()
    local("%s http://en.wikipedia.org/wiki/Neil_Armstrong" % app)

@task
def import_db_local(sql_file):
    """
    Import a SQL file into a local database
    """
    local("mysql database_name < sql_file.sql")

@task
def clone_db_remote_to_local(directory):
    """
    Get a copy of a remote website's db on your local machine.

    Usage:
        fab -H deployuser@example.com clone_remote_db:'/path/to/drupal/site/root'
    """
    path = remote_db_backup(directory)
    sql_file = get_db_dump(path)
    # Ask the user for a clean database
    # Check that the database is clean
    import_db_local(sql_file)

@task
def clear_cache():
    """ Clear the database cache on a Drupal website """
    run("drush cache-clear")
