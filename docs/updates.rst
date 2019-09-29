Updates
=======

============
MB-Lab 1.7.6
============

* Latino model type added
* South American phenotype added
* New Skin shader, MBLab Skin 2 added
* New Nail shader added
* Improved Tongue shader
* Skin tone maps based on character selection added
* New texture masks for procedural elements in MBLabSkin2 added
* Edited Freckle masks
* Removed Specular, SSS, Roughness from texture maps
* Changed structure of humanoid_library.blend
* Added model license types in character selection menu
* Alphabetized the characters list
* Added model license types in character selection menu


============
MB-Lab 1.7.5
============

* Added icons and modified GUI
* Tongue shader added
* Save and Load Bone rotation offsets to file
* Face Rig updated
* Improved Iris shader
* Changed descriptions for male and female elf and dwarf characters
* Changed Blender minimum version to 2.80.74
* Removed Buggy message from Muscle checkbox because the Blender bug has been fixed
* Changed CREATION TOOLS in GUI to CREATION OPTIONS at startup
* Documentation updates
* Changed characters_config.json for tongue shader
* Rebuilt humanoid_library.blend for Blender 2.80
* Reduced SSS value for EEVEE in human skin shader
* Fixed API change 'bpy.context.scene.update()' to 'bpy.context.view_layer.update()' in animationengine.py fixing BVH import bug
* Gloss fix for EEVEE in human skin shader
* Muscle FK and IK, Skeleton FK and IK roll fixes for various bones in armatures
* Edited bump maps

============
MB-Lab 1.7.4
============

* New Procedural Eye shaders
* New Texture Mask for freckles
* Deleted Principled BSDF shader networks for custom surface shaders
* Minor GUI edits
* Edited Bump and Albedo texture maps
* Changed scaling of sub dermal map
* Updated Material Engine code for texture masks
* Added bug warning to Muscle checkbox
* When transferring weights for proxying, check the vertex is in the group
* Changed lighting setup using Area lights
* Set lighting setup default to False, fixing a minor startup bug

==============
MB-Lab 1.7.3
==============

* Added Auto-Updater by CGCookie
* Fixed logging errors left over from original code

============
MB-Lab 1.7.2
============

* Changed Diffuse to Albedo in shaders and textures to reflect current shader terminology
* New Roughness Map
* Added Feet / Inches display in Body Measures panel
* New Docs made with Sphinx

=============
MB-Lab 1.7.1b
=============

* Replace algorithms.print_log_report by python standard logging
* Use numpy to to calculate_disp_pixel
* Code cleanup
* Fixed a spelling typo in facerig.populate_modifiers
* Finalize character fix
* Remove 'self' from args
* Moved is_ik_armature, get_active_armature, get_deforming_armature, get_object_parent to utils.py
* init.py uses get_active_armature and is_ik_armature from utils (previous was algorithms that wasn't imported)
* Armature Toe Bone flipped pose bug fixed
* Proxy Fitting was broken, now it is fixed
* morphengine.py and humanoid.py reverted back to 1.7.0 version with logging added

============
MB-Lab 1.7.1
============

* New Facial Rig connected to shapekeys
* EEVEE and CYCLES specific shading networks
* New Clothes in the Assets directory ready to be added to proxies
* EEVEE Eye shader darker than normal trying to find a fix

=============
MB-Lab 1.7.0b
=============

* Fixed texture map lookup bug for Anime characters
* Fixed a bug with unregistering the add-on
* Anime skin and eye shaders now grouped up
* Moved Dermal and Displacement image import / export to File Tools
* Changed and added missing descriptions

============
MB-Lab 1.7.0
============

* Blender 2.80 Beta code port
* Minor shader node edit to eyes to bring out iris more in renders
* Changes in bump mapping, now uses both procedural and texture map
* Removed skin age
* New SSS Scalable vector node, brings scalable SSS to Principled BSDF
* New bump texture map
* New eye diffuse map for all realistic models

============
MB-Lab 1.6.5
============

* New shading network based on Principled BSDF for skin, eyes and teeth
* New texture maps for specular and subdermal
* Additional code to load new texture maps into the right image texture node
* Added references to new texture maps for all character types
* Changed Skin Editor values to reflect new PBR shading network

============
MB-Lab 1.6.4
============

* Minor edits to skin bump mapping
* Eye shader node tweek
* Procedural freckle generator, basic functionality
* Freckles editable in Skin Editor

============
MB-Lab 1.6.3
============

* Changed button labels to be more uniform
* Minor edits to shader networks
* Basic procedural pore and skin cell bump mapping
* Third layer of SSS added to simulate sub-dermal tissue

============
MB-Lab 1.6.2
============

* New layer of SSS added to skin shader
* Grouped Skin, Eye and Teeth shader networks into easy to edit nodes
* Modified Eye shader, added Diffuse and Glossy network
* Modified Eye shader to reduce red fireflies artifact
* Changed identity, version number, wiki and issue tracker URL
* Changed Blender version from 2,7,9 to 2,79,0
