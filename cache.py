from fabric.api import (run, task)


@task
def clear():
    """ Clear the database cache on a Drupal website """
    run("drush cache-clear all")
