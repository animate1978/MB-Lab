MB-Lab Data
===========

Currently the data of MB-Lab is centralized into a database of JSON files.


======================
humanoid_library.blend
======================

Contains the following

Mesh

    MBLab_human_female
    MBLab_human_male
    MBLab_anime_female
    MBLab_anime_male

Armatures

    MBLab_skeleton_base_fk
    MBLab_skeleton_base_ik
    MBLab_skeleton_muscle_fk
    MBLab_skeleton_muscle_ik

Shaders

Realistic Shaders

    MBlab_pupil
    MBlab_human_teeth
    MBlab_fur
    MBlab_generic
    MBlab_human_eyes
    MBlab_cornea
    MBlab_human_skin
    MBlab_iris

Cell Shaders

    MBlab_toon_black
    MBlab_generic
    MBlab_anime_skin
    MBlab_anime_eyes

FaceRig

    Face_Rig_widgets
    Phenome_rig
    MBLab_skeleton_face_rig

WARNING! Editing humanoid_library.blend can cause irreversible damage! Do not edit unless you know exactly what you are doing!

======================
characters_config.json
======================

The base models, textures and JSON data are referenced from this file


=======================
retarget_knowledge.json
=======================

Retargetting data

=============
anthropometry
=============

Contains measurement data for male and female base models

======
assets
======

Contains the demo asset files, as well as associated texture maps.

======
bboxes
======

(?) Bounding Box?

================
expressions_comb
================

==================
expressions_morphs
==================

======
joints
======

Contains some kind of data related to joints between bones of the armature, is called by skeletonengine.py

========
measures
========

Contains measurement data

======
morphs
======

=======
pgroups
=======

Polygon Indices?

==========
phenotypes
==========

Morphs for each base model that change the character based on geographic location

=====
poses
=====

Pose JSON files for each base model

=======
presets
=======

Morphs to describe different body types

========
textures
========

The texture maps for MB-Lab

Displacement data (Red = Details, Green = Age factor, Blue = Tone factor, Alpha = Mass factor)


===============
transformations
===============

========
vertices
========

Contains vertex info?

=======
vgroups
=======
Contains vertex group data

    Data seems to be [Polygon Indice, Weight Value]

