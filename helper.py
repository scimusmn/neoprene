from fabric.api import hide, settings
from fabric.colors import blue, red
from fabric.contrib.console import confirm
from contextlib import contextmanager
import re


@contextmanager
def mute():
    """Run a fabric command without reporting any responses to the user. """
    with settings(warn_only='true'):
        with hide('running', 'stdout', 'stderr', 'warnings'):
            yield


def header(txt):
    """Decorate a string to make it stand out as a header. """
    wrapper = "------------------------------------------------------"
    return blue(wrapper + "\n" + txt + "\n" + wrapper, bold=True)


def cleanup_drush_output(o):
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
