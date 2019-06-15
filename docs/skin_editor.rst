Skin Editor
===========

MB-Lab provides a procedural skin editor that can be used with Cycles or EEVEE.

.. image:: images/skin_editor_01.png

Behind the simple interface there is a set of complex shaders. The shaders themselves have undergone an evolution since version 1.6.1.

These shaders have been developed to simulate the variety of skin tones and work under any lighting condition. There are currently two sets of shaders, one "photorealistic" set and the "cell" shaders set.

* An advanced human skin shader
* An advanced toon skin shader
* Procedural eyeball and iris shaders
* Shaders for the teeth and tongue

These shaders have been developed for Cycles and EEVEE and continue to be worked on as MB-Lab evolves.

.. image:: images/skin_shader_01.png

The following paramter editor will change depending on the base model you choose. The parameters editor is composed by an intuivive set of sliders for easily modify the values of skin complexion, skin bump, skin oil, skin saturation, skin subsurface scattering and more.

===========================
Realistic Shader Parameters
===========================

The realistic skin shader set is linked to the realistic base models.

---------------
Skin complexion
---------------

One of most important parameters is the complexion. It modifies the color in order to vary from very light skin to very dark one. It's not just the brightness, but a complex result obtained using the samples from an image included in the lab data.

.. image:: images/gallery_150_13.png

--------
Skin oil
--------

Another important factor is the amount of the oil layer. It's a thin layer that protects the skin, more noticeable in some body parts and almost invisible in others.

---------
Skin bump
---------

This parameter controls the amount of the skin bump. It doesn't affect the true displacement of the subdivided mesh, but only the visual bump effect calculated at render time.

--------------
Skin Roughness
--------------

This controls the micro scale roughness

-------------
Skin Freckles
-------------

This parameter controls how much procedural freckles are added

----------
Skin Veins
----------

This controls how much procedural veins are added to the skin

-------
Eye SSS
-------

This controls how much subsurface scattering of the eye is rendered

---------------
Eye Vein Amount
---------------

This controls how much veins are visible on the eyeball

--------------------------
Bump/displacement controls
--------------------------

The button "Update displacement" is the gui for the displacement system, an algorithm that automatically creates the bump map from the values of age, mass and tone parameters.

You should use this button to update the bump/displacement each time you change the meta parameters. Note that to see these changes in realtime, you need to enable some display options.

Each time the button "Update displacement" is pressed, the system recalculates the displacement map using the values of meta parameters. This map can be saved with the "Save displacement image" button, in order to be usable in external engines or in finalized characters.

======================
Cell Shader Parameters
======================

The "Cell" shaders have some different sliders for this set, be aware that the EEVEE and Cycles rendering will be slightly different due to how the shader works. Also note that this shader is very fast and you will be able to see changes in near real time with EEVEE as well as Cycles.

-------------
Skin oil size
-------------

This controls the "oil" of the cell shader, this effect can bring out the contour of the characters.

---------------
Skin oil values
---------------

This controls how brightness of the "oil"

-----------------
Skin Outline size
-----------------

This controls the thickness of the outline of the characters

------------------
Skin Outline value
------------------

This controls how dark the outline will be

-------------------
Skin Secondary size
-------------------

This will add another shade to the cell shader, showing even more contour, warning this effect is only seen in Cycles currently

--------------------
Skin Secondary value
--------------------

This changes the color value of the Secondary cell shading
