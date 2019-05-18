MB-Lab Modules
==============

===========
_ init _.py
===========
This is the core of the addon.

* Function calls
* UI Elements

=============
algorithms.py
=============

Contains various functions for every engine.

* Example - https://github.com/animate1978/MB-Lab/blob/3994f37e33699bd0d082a4f9f076724e4f0d40ba/algorithms.py#L1332

==================
animationengine.py
==================
Handles the animation import and assigning to skeleton...

* Retargeting
* Identifies Bones
* Similar functions (expand)
* Loads BVH files, saves and loads poses.

===========
humanoid.py
===========

Handles much of the character changing functions including Auto-Modelling.

=================
materialengine.py
=================

This is where the image textures get loaded and applied to nodes

==============
morphengine.py
==============

This is where the morphs of the character are loaded from JSON files


==============
proxyengine.py
==============
Handles the Proxy Fitting functions

=================
skeletonengine.py
=================

Loads and applies the skeleton (either FK or IK) to the character
