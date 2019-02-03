Finalize
========

In order to be modified with the lab tools during the creation phase, a model created with the lab has some special requirements:

    Its name must be recognizable by the lab
    It can't include shape keys
    It can't be customized (for example in edit mode or via sculpting)
    It's not possible to add or remove vertices
    It has many custom properties
    It uses directly the textures from lab data so they can't be customized.
    It's the unique lab character in the scene

To remove these limits and enable the "after-creation" tools, the lab model must be converted in a normal model, using the finalization process.
The production pipeline and finalization step

The lab is optimized for a pipeline where

    The lab is used to create the character.
    The character is saved or exported as lab file in a "character archive" folder (see: Save and export the character for further details)
    The character is converted in a normal Blender model (finalized).
    The character now can be customized in edit mode and used as any other normal character. It can be exported in any format supported by Blender or appended in another Blender scene for final production.

Finalization effect and options

The third step is very important.

The finalization is a process to clean all the custom properties, select the rest pose, add a set of standard shape keys for expressions and transform the lab character in a normal character for Blender, not linked to the lab script, that can be handled as any other normal model in Blender.

So the finalized character will have:

    A rigged armature
    A set of standard shapekeys for expressions
    A subdivision surface modifier
    A corrective smooth modifier
    A displacement modifier
    A set of materials for skin, eyes, etc
    An action with the animation

The finalize panel includes some important options.

the finalize panel

The finalize section includes two options.

    Save images and backup charater. To export the textures in your custom folder and backup the character as json file. The new path of the images will be stored in the shader, and it will be editable as usual in Blender node editor or Blender material editor. The backup file will permit to restore the character using the "import character" button.
    Remove modifiers. All modifiers (subsurface, displacement, corrective smooth, etc..) except the armature modifier will be removed from the finalized character.

To finalize the character, just press the button "Finalize". It's located at the bottom of the lab panel. There is no undo for this operation.

The finalization process is NOT reversible and it will convert the lab model in a normal model, so it will lose all the lab functionalities and it will be not editable with the lab tools.

For this reason the option "Save images and backup charater" is very important and it's enabled by default.
