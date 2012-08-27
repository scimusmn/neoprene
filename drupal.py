def db_backup(directory):
    """
    Uses drush and the Backup and Migrate modual to make sql dump of the
    database for the spcified site.

    Returns the full filepath to the backup
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
        file = r.group(1) ".mysql.gz"
        o = run("drush vget file_private_path")
        r = re.match('file_private_path: "([^"]*)"', o)
        path = r.group(1) "/backup_migrate/manual/"
        filepath = directory path file
        return filepath

def clear_cache():
    """
    Clear the database cache on a Drupal website
    """
    run("drush cache-clear")


