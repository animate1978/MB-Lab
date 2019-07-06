Installation
============

==============
Install MB-Lab
==============


**IMPORTANT**

Because of how Github packages releases, this WILL affect how you install MB-Lab if downloading from the release page ONLY!

If you download a clone where Github renames it **MB-Lab-master**, you will not have issues.

You need to go to that directory and rename it from **MB-Lab 1.x.x** to **MB-Lab-1-x-x** or **MBLAB175** if you want to be simple, **just get rid of the periods in the directory name** and Blender will recognize it and add the addon to the list.

* Step 1

In Blender 2.80, open the user preferences window, choosing Edit → Preferences


.. image:: images/install_01.png


* Step 2

Press the "Install" button in the top right side of the window


.. image:: images/install_02.png


* Step 3

Use the file selector window in order to find the zip file, select it and click the button "Install Addon from File".


.. image:: images/install_03.png



* Step 4

When the installation will be completed, a new category named "Characters" will appear in the Categories list. Select it and enable the lab using the check button. When the plugin is enabled, remember to press the button "Save User Settings", in order to load the lab automatically each time you start Blender.


.. image:: images/install_04.png



* Step 5

Close the User Preferences window.

Press "N" to make the Sidebar with the MB-Lab interface appear in Blender 2.80

.. image:: images/new_GUI_001.png



================
Uninstall MB-Lab
================

In Blender, open the user preferences window, choosing File → User Preferences

In the addon tab, look for Characters → MB-Lab

.. image:: images/remove_01.png


Click on "Remove" button

It is VERY important to not have multiple copies of ManuelBastioniLAB or MB-Lab, there will be conflicts! Remove the old version first, then install from file the new version.

=============================
MANUAL INSTALLATION / REMOVAL
=============================

You can manually install MB-Lab as well. You need to unzip MB-Lab to the following directories for your OS.

* Windows 7 - C: \ Users \ USERNAME \ AppData \ Roaming \ Blender Foundation \ Blender \ 2.80 \ scripts \ addons

* Windows 10 - C: \ Users \ USERNAME \ AppData \ Roaming \ Blender Foundation \ Blender \ 2.80 \ scripts \ addons

* Linux - /home/USERNAME/.config/blender/2.80/scripts/addons/

* MacOS - ~/Library/Application Support/Blender/2.80/scripts/addons/

To remove simply delete the MB-Lab directory from your file system

=========
Upgrading
=========

With **MB-Lab 1.7.3** it is now possible to upgrade the addon inside Blender without having to go through a lot of extra steps of cloning the repository, downloading the addon and installing every time there is an update to MB-Lab.

.. image:: images/auto_updater_173.png

To update go to Edit → Preference → Addons and then check the arrow to expand the addon information.

To update MB-Lab to latest version in the 'master' branch, click on "Update mb_lab addon now"

You can also set the addon to automatically check, by setting the Interval between checks. There are options for Months, Days, Hours and Minutes. It is recommended to check every 2 weeks to a month based upon the update history of MB-Lab.

