Skin Editor
===========

MB-Lab provides a procedural skin editor that can be used with Cycles or EEVEE.

.. image:: images/skin_editor_01.png

Underneath the Skin Editor is a set of complex surface shaders. These shaders have been in constant development since version 1.6.1 

These shaders have been developed to simulate the variety of skin tones and work under any lighting condition. There are currently two sets of shaders, one "photorealistic" set and the "cell" shaders set. Each set of shaders are assigned to specific base models.

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

This controls the sheen value of the skin oil. The roughness value also affects the visual result of the oil.

.. image:: images/SS_oil_00.png
.. image:: images/SS_oil_90.png

--------------
Skin Roughness
--------------

This controls the micro scale roughness. This value helps control how much skin oil is also visible.

.. image:: images/SS_rough_00.png
.. image:: images/SS_rough_090.png

---------
Skin bump
---------

This parameter controls the amount of the skin bump. It doesn't affect the true displacement of the subdivided mesh, but only the visual bump effect calculated at render time.


-------------
Skin Freckles
-------------

This parameter controls how much procedural freckles are added, the visibility is affected by a texture mask

----------
Skin Veins
----------

This controls how much procedural veins are added to the skin

.. image:: images/SS_skinveins_000.png
.. image:: images/SS_skinveins_100.png

--------
Skin SSS
--------

This controls the overalll Sub Surface Scattering of the skin

.. image:: images/SS_SSS_000.png
.. image:: images/SS_SSS_100.png

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

=======================
Post Finalization Notes
=======================

Once you finalize the MB-Lab character it is NOT required to have the surface shaders currently shipped with, if your production needs differ from the shaders assigned it is fully possible to add your own shaders.

Each base model has shaders assigned to polygons, these shaders can easily be replaced with your own simply by replacing the current ones shipped.

This also applies to the texture maps that are shipped with MB-Lab, these can be edited by your prefered image editor (such as Photoshop or GIMP) to your specfic needs.

============
Future Notes
============

The surface shaders are always undergoing evalution and testing to try to achieve the best possible visual representation of the human body.

One feature that is being developed for future versions of MB-Lab is a fingernail shader that will hopefully allow users to change the color. This will also apply to toe nails.

It has been suggested that features such as scars or tattoos should be added, this unfortanatly cannot be completed because of the variable nature of such "features", one cannot predict or dictate these features without having a MASSIVE library for them and as such these will NOT be added to MB-Lab. If your production needs require such features it is recommended that you create edited versions of the texture maps supplied, change shader networks and whatever else is needed to complete the character AFTER finaliztion.

If you have suggestions about the surface shaders please feel free to contact the developers.