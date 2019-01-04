# CHANGE LOG

All changes will be documented here

# MB-Lab 1.7.0b

## Bug fixes

 - Fixed texture map lookup bug for Anime characters
 - Fixed a bug with unregistering the add-on

## Changed

 - Anime skin and eye shaders now grouped up
 - Moved Dermal and Displacement image import / export to File Tools
 - Changed and added missing descriptions


# MB-Lab 1.7.0

## Blender 2.80 Update!

 - Blender 2.80 Beta code port done by Amir Shehata amir.shehata@gmail.com

## Changed

 - Minor shader node edit to eyes to bring out iris more in renders
 - Changes in bump mapping, now uses both procedural and texture map
 - Removed skin age

## Added

 - New SSS Scalable vector node, brings scalable SSS to Principled BSDF
 - New bump texture map
 - New eye diffuse map for all realistic models


# MB-Lab 1.6.5

 - New shading network based on Principled BSDF for skin, eyes and teeth
 - New texture maps for specular and subdermal
 - Additional code to load new texture maps into the right image texture node
 - Added references to new texture maps for all character types
 - Changed Skin Editor values to reflect new PBR shading network

# MB-Lab 1.6.4

## Changed

 - Minor edits to skin bump mapping
 - Eye shader node tweek

## Added

 - Procedural freckle generator, basic functionality
 - Freckles editable in Skin Editor

# MB-Lab 1.6.3

## Changed

- Changed button labels to be more uniform
- Minor edits to shader networks

## Added

- Basic procedural pore and skin cell bump mapping
- Third layer of SSS added to simulate sub-dermal tissue

# MB-Lab 1.6.2

## Changed

- New layer of SSS added to skin shader
- Grouped Skin, Eye and Teeth shader networks into easy to edit nodes
- Modified Eye shader, added Diffuse and Glossy network
- Modified Eye shader to reduce red fireflies artifact
- Changed identity, version number, wiki and issue tracker URL
- Changed Blender version from 2,7,9 to 2,79,0
