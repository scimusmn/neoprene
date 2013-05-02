# Fabric modules
from fabric.api import (cd, env, get, local, prompt, run, task)
from fabric.contrib.files import (exists)

# Neoprene modules
from . helper import cleanup_drush_output, header, mute

# Python modules
import re


@task
def dump_remote(directory):
    """Use Backup and Migrate to make a SQL dump of a website's the Database

    Usage:
        fab -H example.com dump_remote:'/site/path/'

    Returns:
        The full filepath to the backup
    """
    with cd(directory):
        o = run("drush bam-backup")
        r = cleanup_drush_output(o)
        # Get the backup filename from the response
        r = re.match('Default Database backed up successfully to ([^\s]*) '
                     'in destination Manual Backups Directory in '
                     '[\d]*\.[\d]* ms.',
                     r)
        bam_filename = r.group(1) + ".mysql.gz"

        # Get the path to the Drupal files directory, silently
        with mute():
            drupal_files_path = run("drush dd files")
            bam_path = drupal_files_path + "/backup_migrate/manual/"

        with cd(bam_path):
            bam_filepath = env.cwd + bam_filename
            return bam_filepath


@task
def local_db_import(local_db_name, local_sql_file, local_db_host='localhost',
                    local_db_user=None, local_db_pass=None):
    """
    Import a SQL file into a local database
    """
    with mute():
        db_import_cmd = "mysql -h %s -u %s" % (local_db_host, local_db_user)
        if local_db_pass is not None:
            db_import_cmd = db_import_cmd + " -p %s" % local_db_pass
        db_import_cmd = db_import_cmd + " %s < %s" % (local_db_name,
                                                      local_sql_file)
        local(db_import_cmd)


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
            with mute():
                db_response = local(create, True)
                return db_response


def interactive_create_db(place, db_host, db_user, db_pass):
    """
    Keep asking the user for a database name until the create function
    stops returning errors.
    """
    error_code = 1
    while error_code == 1:
        # Ask the user for a clean database
        txt = "What would you like to call you local database?"
        print
        db_name = prompt(txt)
        db_response = create(place, db_name, db_host, db_user, db_pass)
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
        fab -H example.com pull_db:'/path/to/drupal/site/root'
    """
    txt = "Getting a database backup of your remote site."
    print
    print header(txt)
    print

    path = dump_remote_db(directory)
    localpath = get(path, "/tmp")
    gz_file = localpath[0]
    local("gunzip %s" % gz_file)
    sql_file = re.sub('\.gz$', '', gz_file)

    txt = "Importing the database on your local machine."
    print
    print header(txt)

    if local_db_user is None:
        with mute():
            local_db_user = local('whoami', True)

    print "Writing to your local database using these credentials:"
    print "  hostname: %s" % local_db_host
    print "  username: %s" % local_db_user
    if local_db_pass is None:
        print "  password: defined in ~/.my.conf"
    else:
        print "  password: ***"

    # Create and import db
    db_name = interactive_create_db('local', local_db_host, local_db_user,
                                    local_db_pass)
    print
    print "Importing the database..."
    local_db_import(db_name, sql_file, local_db_host, local_db_user,
                    local_db_pass)
    print
    print "...done. Your database, %s is ready to go." % (db_name)

    print
    print "Cleaning up."
    local("rm -f sql_file")


@task
def local_db_list(batch=False):
    """
    List databases. If desired print the output in MySQL's batch Modernizr
    which will not print table decoration.
    """
    if batch == 'True':
        batch_option = '--batch '
    else:
        batch_option = ''
    local('mysql %s-e "show databases;"' % batch_option)


def get_mysql_pass():
    """Find out if we have the right information to use MySQL"""

    # There is a password file and it has a password in it.
    with mute():
        if mysql_cnf_exists() and mysql_cnf_password_set():
            password = run('awk < ~/.my.cnf -F"=" \'{ print $2 }\'')
            return password


def mysql_cnf_exists():
    with mute():
        if exists('~/.my.cnf'):
            return True
        else:
            return False


def mysql_cnf_password_set():
    """Check to see if a password is set in my.cnf """
    with mute():
        if mysql_cnf_exists():
            if run("grep 'password.*=' < ~/.my.cnf"):
                return True
            else:
                return False
