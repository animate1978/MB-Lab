New Features
============

=============
Version 1.7.6
=============

This version features a few new features!

* Latino model type

This version includes a new model type, the Latino model type as well as a new South American phenotype

* Skin tone for each model type

Now the skin tones by default will load per model type

* MB-Lab Skin 2

This is a completely new skin shader, using more procedural elements than previous versions, eliminating a lot of texture maps for simple rendering functions (Specular, SSS, Roughness etc...)

* Fingernail shader

This is a new shader for fingernails (current human female base mesh)


=============
Version 1.7.5
=============

This version is meant to be the "official" stable version for Blender 2.80 after it is officially released.

* GUI change

This version shows the evolution of the GUI that has changed since the original 1.6.1 version.

Icons have been added everywhere now!

.. image:: images/GUI_175.png

* Improved Face Rig

The Face Rig has been updated now, with a new FACS capable Rig



* Tongue Shader

Now you can edit the skin complexion without changing the color of the tongue.

.. image:: images/tongue_001.png

* Improved Eye and Iris Shaders

This was a very late addition to MB-Lab 1.7.5 but looks fantastic compared to the previous versions

.. image:: images/new_eyes_04.png

* Animation BVH Files

These are "raw" BVH files of some basic animations such as walking, running, jumping etc...

* BVH Bone Config

Save and load config files to adjust bones after importing BVH animation files.

.. image:: images/bone_offset_01.png


=============
Version 1.7.4
=============

Shaders for this version have been re-worked from the ground up to try to achieve a realistic look as much as possible.

The skin shader has dropped the Principled BSDF node in favor of a new custom node network.

Procedural veins have been added. The visibility of the veins are controlled by a slider in the skin editor.

The eyes have become completely procedural in this version, which allows a greater range of color for the iris than before.

Eye vein visiblity is controlled with a slider.

The lighting setup has been changed to a three point arrangment using Area lights now.


=============
Version 1.7.3
=============

This version is the addition of the Auto Updater.

.. image:: images/auto_updater_173.png

This will allow users to update to new versions of MB-Lab without having to go to Github or reclone manually.

The updater can auto check at a user defined set interval.

The updater also can make backups of MB-Lab so if by chance a buggy version is released, this can revert back to working version.

The only downside is that the updater works from version 1.7.3 onward so it is not possible to revert back to previous versions, so this makes it a pretty important update as well.
