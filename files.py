# Fabric modules
from fabric.api import (cd, run, task)
from fabric.contrib.files import (contains, exists, sed)


def check_rewrite_base_enabled(path):
    """Check to see if RewriteBase is enabled on a Drupal site

    Args:
        path: Full path to a Drupal website

    Returns:
        A boolean. True is RewriteBase is enabled, False if not.
    """
    htaccess = path + '/.htaccess'
    # Look for an existing RewriteBase directive
    if contains(htaccess, "^.[^#]*RewriteBase \/.*$", escape=False):
        return True
    else:
        return False


@task
def enable_rewrite_base(path, base=None):
    """Change the RewriteBase variable on a Drupal site

    Args:
        parent: Path to the website base
        base: RewriteBase string to add to the .htaccess file (default: None)

    Usage:
        $ fab -H localhost enable_rewrite_base:'/path/to/web/dir/site-name','site-name'

        Will modify the .htaccess file at /path/to/web/dir/site-name/.htaccess
        adding this RewriteBase directive:
            RewriteBase /site-name

        $ fab -H localhost rewrite_base_enable:'/path/to/web/dir'

        Will modify the .htaccess file at /path/to/web/dir/.htaccess
        adding this RewriteBase directive:
            RewriteBase /
    """
    htaccess = path + '/.htaccess'
    if exists(htaccess):
        if not check_rewrite_base_enabled(path):
            # sed the RewriteBase rule
            sed(htaccess, "^.*# RewriteBase /$", "  RewriteBase " + base)


@task
def setup_files(path):
    """
    Setup the Drupal files directory

    Usage:
        fab -H localhost setup_files:'/path/to/site'
    """
    with cd(path):
        # Setup files
        run("mkdir -p sites/default/files/private")
        #run("chown -R apache:www sites/default/files")
        run("chmod -R ug+ws sites/default")


@task
def setup_settings(path, db_name):
    """
    Setup the Drupal settings.php file

    Usage:
        fab -H localhost setup_settings:'/path/to/site'
    """
    path = path + '/sites/default'
    with cd(path):
        run("cp -v default.settings.php settings.php")
