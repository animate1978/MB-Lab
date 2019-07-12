# MB-Lab

Character creation tool for Blender

## Blender 2.8 Support

MB-Lab has been developed to work with Blender 2.80

## Contributors wanted! Python programmers needed!

We are a small bunch of developers and artists but we always need more! MB-Lab's code is quite complex and needs work, to either fix bugs or to add new features, Python programmers are always welcome! Do you have other skills? We need modelers to help with future base models for instance. Are you a specialist in rigging? We could use some help improving the rigs for MB-Lab. There are lots to do in this project, we can only do so much at a time so please feel free to join us, fork the repository and then make something cool.

## About

MB-Lab is a community developed and supported project based off ManuelBastioniLAB.

This fork is an attempt to keep this addon going forward as the original author is no longer developing ManuelBastioniLAB

# MB-Lab 1.7.5

## Added

- Added icons and modified GUI
- Tongue shader added
- Save/Load BVH Bone Config

## Changed

- Improved Iris shader (PENDING)
- Changed descriptions for male and female elf and dwarf characters
- Changed Blender minimum version to 2.80.74
- Removed Buggy message from Muscle checkbox because the Blender bug has been fixed
- Changed CREATION TOOLS in GUI to CREATION OPTIONS at startup
- Documentation updates
- Changed characters_config.json for tongue shader
- Rebuilt humanoid_library.blend file for Blender 2.80.74
- Reduced SSS value for EEVEE in human skin shader
- Edited bump maps
- Changed "Body Measures" in "Body Measures" to "Measurements" to fix confusion

## Bug Fixes

- Fixed API change 'bpy.context.scene.update()' to 'bpy.context.view_layer.update()' in animationengine.py fixing BVH import bug
- Gloss fix for EEVEE in human skin shader
- Muscle FK and IK, Skeleton FK and IK roll fixes for various bones in armatures
- Registration bug that caused errors during unregistering classes
- Fix 'Bones rot. offset' in after-creation tools
- Fixed Skin complexion function related to SSS
- Toes_R connected bug fixed

## ManuelBastioniLAB 1.6.1a

We are including this for historical purposes as the website, videos and social media accounts are offline.

The version 1.6.1a of ManuelbastioniLAB, the free and open source character editor for Blender, ~~is still available for download at http://www.manuelbastioni.com~~
Direct download: [manuelbastionilab_161a.zip](https://github.com/NumesSanguis/FACSvatar/releases/download/v0.3.4-alpha-release/manuelbastionilab_161a.zip)
