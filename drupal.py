def db_backup(directory):
    """
    Uses drush and the Backup and Migrate modual to make sql dump of the
    database for the spcified site.
    """
    with cd(directory):
        output = run("drush bam-backup")
        # Get the backup filename from the response
        r = re.match('Default Database backed up successfully to '
                      '([^\s]*) '
                      'in destination Manual Backups Directory in '
                      '[\d]*\.[\d]* ms\.[\s]*\[success\]',
                      output
                    )
        backup_file = r.group(1)

def clear_cache():
    """
    Clear the database cache on a Drupal website
    """
    run("drush cache-clear")


