<img width="239" height="300" align="right" alt="Image of Wallace Carothers stretching Neoprene" src="/media/carothers.jpg" />

# Neoprene:<br />Deploy & administer Drupal websites<br />using Python and Fabric

### Warning
This is alpha code and is actively being developed and might break your systems. Please test before using on anything you care about.

## Usage
* Include this module in your application's fabfile.py to utilize these Drupal specific tasks.

## About
* [Fabric](http://docs.fabfile.org) is a Python library for application deployment and system administration tasks. [Neoprene](https://github.com/scimusmn/neoprene) is a library that aids in common [Drupal](http://www.drupal.org) deployment and system administration tasks, using Fabric.
* Neoprene assumes you have [Drush](http://drupal.org/project/drush) installed on your remote and local systems.

## Install (required)

### Install Python 
Links to various tips about this for your OS should go here.

### Install Fabric
As of 2013_03_28 you'll need the latest dev version of Fabric. There's a bug in the latest solid release that makes `sed` not work on a Mac.

To install the dev version do:

    pip install paramiko==dev
    pip install fabric==dev

Paramiko is a Python SSH library.

# Misc.
Q: Who's that guy in the picture?

A: Why, that's [Wallace Carothers](http://en.wikipedia.org/wiki/Wallace_Carothers) stretching a peice of Neoprene. He's the the organic chemist who invented Nylon and helped lay the groundwork for the invention of Neoprene...the material...not this software.
