# MB-Lab

Character creation tool for Blender

## Blender 2.8 Support

MB-Lab has been developed to work with Blender 2.80

## Contributors wanted!

We are a small bunch of developers and artists but we always need more! MB-Lab's code is quite complex and needs work, to either fix bugs or to add new features, Python programmers are always welcome! Do you have other skills? We need modelers to help with future base models for instance. Are you a specialist in rigging? We could use some help improving the rigs for MB-Lab. There are lots to do in this project, we can only do so much at a time so please feel free to join us, fork the repository and then make something cool.

## About

MB-Lab is a community developed and supported project based off ManuelBastioniLAB.

This fork is an attempt to keep this addon going forward as the original author is no longer developing ManuelBastioniLAB

# MB-Lab 1.7.7

## Added

- Hair System added
- Human Rotation Limits added
- New option to fit in reverse direction to convert a character-specific mesh to a generic proxy.
- New options to do more precise fitting by turning off some normally useful smoothing passes.

## Changed

- Afro Female now the default character on startup
- Updated GUI
- Removed Docs from project directory to it's own repository

## Bug Fixes

- Certain bones have to be precisely aligned to the rotation of a specific other bone, which required new code.
- Stretch to has to be applied to the muscle bones while fitting.
- B-Bone handles and certain constraints have to be fixed in the library file via a script.
- Fixed fitting of meshes that are very close to the skin.
- Replaced obj.hide_select = False with obj.hide_set(False) fixing Age update bug.
- Minor GUI edits to fix drawing issues.
- Fixed Bump and Displacement issues in MBLab_Skin2
- Fixed IK and IK/Muscle bugs

## Known Issues

## ManuelBastioniLAB 1.6.1a

We are including this for historical purposes as the website, videos and social media accounts are offline.

The version 1.6.1a of ManuelbastioniLAB, the free and open source character editor for Blender, ~~is still available for download at http://www.manuelbastioni.com~~
Direct download: [manuelbastionilab_161a.zip](https://github.com/NumesSanguis/FACSvatar/releases/download/v0.3.4-alpha-release/manuelbastionilab_161a.zip)
