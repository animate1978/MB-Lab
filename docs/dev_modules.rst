MB-Lab Modules
==============



============
Main Modules
============

The main modules are derived from the original code of ManuelBastioiLAB ver 1.6.1

Since the beginning of the fork this code has evolved and expanded over time.

-----------
_ init _.py
-----------
This is the core of the addon.

* Function calls
* UI Elements

-------------
algorithms.py
-------------

Contains various functions for every engine.

* Example - https://github.com/animate1978/MB-Lab/blob/3994f37e33699bd0d082a4f9f076724e4f0d40ba/algorithms.py#L1332

------------------
animationengine.py
------------------

Handles the animation import and assigning to skeleton

* Retargeting
* Identifies Bones
* Similar functions (expand)
* Loads BVH files, saves and loads poses.

-----------
humanoid.py
-----------

Handles much of the character changing functions including Auto-Modelling.

-----------------
materialengine.py
-----------------

This is where the image textures get loaded and applied to nodes

--------------
morphengine.py
--------------

This is where the morphs of the character are loaded from JSON files


--------------
proxyengine.py
--------------

Handles the Proxy Fitting functions

-----------------
skeletonengine.py
-----------------

Loads and applies the skeleton (either FK or IK) to the character

===========
New Modules
===========

The new modules have been added over time to support the main code.


-------------
hairengine.py
-------------

This is the code that applies the hair to MB-Lab characters

-----------
file_ops.py
-----------

Contains code that handle file operations

---------------
material_ops.py
---------------

Contain functions that control some of the materials in MB-Lab

-------------
object_ops.py
-------------

Contain functions that help in object manipulation

----------
facerig.py
----------

This is the code that controls the face rig

--------------
preferences.py
--------------

Related to the Auto-updater

--------
utils.py
--------

Contain helper code for other engines

---------------------
humanoid_rotations.py
---------------------

Contains code for the human rotation limit feature

=====================
Addon Updater Modules
=====================

----------------
addon_updater.py
----------------

The main code for the auto-updater

--------------------
addon_updater_ops.py
--------------------

Contains functions and the settings for the auto-updater