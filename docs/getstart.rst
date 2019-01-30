Getting Started
===============

The user interface is perfectly integrated in Blender and designed to make the modelling process a simple and clear activity.

MB-Lab is designed for a production pipeline divided in two main steps:

* Creation phase: definition of the body, the physiognomy and the appearance of the character. The model will be characterized with age, muscles, mass, face details, measures, skin shader and skin textures. This phase also includes the random generator, the automodelling, the character library, the definition of rest pose and the type of rigging to use (for example with inverse kinematic or not).
* After-creation phase: use of finalized model during production. This phase includes the loading of poses and animation (with automatic retarget) the control of the expressions and the automatic fitting of proxies (clothes, hair).

These two phases are reflected in the organization of the interface, that is divided in two parts. The upper section is for the creation step, while the lower section is for after-creation work.



NOTE: The "after-creation" section is hidden during the creation step. It's automatically enabled only for finalized characters.

At the start the creation section contains only few elements:

* The selector to choose the base model
* The option related to the type of skeleton (basic, with inverse kinematic, with bending muscles)
* The create button to initialize it
* Some options related to rendering engine and lights

MB-Lab includes a set of base characters, as shown in the figure:

Pressing the "create character" button, Blender will create the selected model, placing it in the centre of the scene, at coordinates 0,0,0.

MB-Lab was redesigned for Blender 2.80 and now has shading networks for both Cycles and EEVEE.

The option "Use portrait studio lights" is to create a set of lights already scaled and normalizated in order to reproduce a professional studio setup.
Note: the scale is one BU (Blender Unit) = one meter.

The system has to import some hundreds of morphings, so it requires some time to complete. At the end of the process the character will be ready for modification.
