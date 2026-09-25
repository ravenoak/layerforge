# Alignment requirements

This page says what LayerForge should do so that cut layers can be stacked in exactly one way. **None of it is built yet.** The [Requirements](requirements.md) page lists what the tool does today. Its [Known gaps](requirements.md#known-gaps) cite the IDs below (TR-1 and so on) to show which target closes which gap.

The same target is written as a formal specification in [`specs/alignment.allium`](https://github.com/ravenoak/layerforge/blob/main/specs/alignment.allium). The rule names there match the IDs here.

## What the owner decided

These facts drive every requirement below. They came from the project owner on 2026-09-24.

- Layers are cut from flat sheet, for example with a laser. A person stacks the cut layers to rebuild the solid.
- A reference mark is a hole cut through the sheet. Holes let a person align opaque layers by eye.
- Every layer must be alignable to the layer below it and the layer above it.
- There must be exactly one way to rebuild the model. Nothing may be ambiguous.
- Each layer carries its number. The person cutting chooses to engrave it (marked on one side only) or to cut it through (readable only from the correct side).
- Units are configurable and default to millimetres.
- A later version may set aside some holes as **dowel holes**. They carry a size and shape of their own and are separate from the alignment marks.

## Terms

| Term | Meaning |
|---|---|
| Layer | One slice of the model, cut from one sheet. The SVG is its view from above (the +z side). |
| Piece | One polygon of a layer, with its holes. A layer can have several pieces. |
| Adjacent pieces | A piece in layer *i* and a piece in layer *i*+1 whose regions overlap by at least `checks.min_overlap_area`. The default is 0, so any overlap counts. |
| Reference mark | A hole cut through the layer that helps align it. Also called an alignment hole or registration hole. The code keeps the name "reference mark". |
| Shared mark | A reference mark that is a hole in both of two adjacent pieces. |
| Footprint | The outline of a mark's hole, not only its centre. |
| Number | The layer number printed on each piece. |
| Dowel hole | A hole sized for a dowel. Planned for a later version, see TR-15. |
| Unit | The length unit set by `--units`. The default is mm. |
| Setting | A number or choice the person can change, with a default. Each has a config-file key such as `marks.size`. See TR-16. |

## How alignment is judged

Three jobs are split between the number and the marks.

| Job | Done by | How |
|---|---|---|
| Face up or flipped | The number | Text reads correctly from one side only. |
| Rotation | The shared marks | No rotation other than none maps the marks, with their shapes and directions, onto themselves. |
| Position and precision | The shared marks | The marks pin the position. Their distance apart sets how well they fix rotation. |

Each case below is a check the tool can run.

| Shared marks on the piece pair | Rotation fixed? | Flip fixed by |
|---|---|---|
| One mark with a direction (triangle, arrow) | Yes | The number |
| One circle or one square | No. A circle has no direction and a square repeats every 90°. | Not enough. Rejected. |
| Two marks of different shapes | Yes. A 180° swap would exchange the shapes. | The number |
| Two identical circles or squares | No. A 180° swap maps them onto themselves. | Not enough. Rejected. |
| Three or more marks with all side lengths different | Yes | The marks themselves |

## Requirements

All rows are **planned**. "Closes" names the known gaps the row addresses, with the issue number in brackets.

### Alignment

| ID | Requirement | Closes |
|---|---|---|
| TR-1 | The layers, each placed with its number readable from above, can be assembled in exactly one way. | Goal |
| TR-2 | Take any two adjacent pieces (see Terms). At least one shared mark exists, and no rotation other than none maps the set of shared marks onto itself. Two marks are the same only if shape, size and angle match. Every piece meets this with each piece it overlaps in the layer above and in the layer below. The lowest and highest layers have one neighbour. | G-4 (#60) |
| TR-3 | The number fixes whether a layer is face up. An engraved number shows on one side only. A cut number reads correctly from one side only. The rule for the person assembling is: place each layer with its number readable from above. The marks do not have to break mirror symmetry. | G-4 (#60) |
| TR-4 | When two or more marks are shared, the two farthest apart are at least the minimum baseline apart. A shorter baseline is a warning. A single shared mark has no baseline. Its own size sets the precision. The baseline is `marks.min_baseline_factor` × mark size. The default factor is 4 (proposed). | G-4 (#60) |

### Reference marks

| ID | Requirement | Closes |
|---|---|---|
| TR-5 | A reference mark is a hole. Its footprint is a closed outline that lies wholly inside the piece. The centre is at least `--mark-min-distance` from every outline of the piece, holes included. The footprints of two holes are at least `marks.min_web_ratio` × layer height apart. The default ratio is 0.5. No footprint overlaps the number. The footprint is checked, not only the centre. | G-21 (#85) |
| TR-6 | The default mark size is the larger of `marks.min_hole_ratio` × layer height and `marks.min_hole_kerf_factor` × `kerf`. The layer height is the sheet thickness. The defaults are 1 and 1.5, so with a 3 mm sheet and 0.3 mm kerf the size is 3 mm. `--mark-size` sets a size. A size below that minimum is a warning, not an error, because the person knows the machine. The size does not depend on the model's size. The default `--mark-min-distance` is the mark size. | G-6 (#62), G-19 (#76) |
| TR-7 | Every shape has a closed outline (a circle or a polygon), anchored at its centre. Its size is the diameter of the smallest circle around the anchor that holds the outline. Angle 0 points along +x and angles turn counter-clockwise. Angles are radians in the package and degrees on the command line. Each shape states its rotational symmetry: circle unlimited, square 4, triangle 1 (isosceles), arrow 1 (a closed arrow outline). | G-20 (#84) |
| TR-8 | The tool chooses shapes so that TR-2 holds. A piece with room for one mark gets a shape with a direction. Two marks on a piece differ in shape, or use shapes with a direction. `--available-shapes` limits which shapes it may use. It no longer sets an order. Shape, size and angle are the same wherever a mark appears. | G-5 (#61) |
| TR-9 | Marks are local to pairs of layers. A mark stays in use while it remains valid in the next layer and is retired when it leaves the outline or clearance. Marks for two adjacent layers are chosen inside the overlap of their outlines, shrunk by the clearance of TR-5, so each shared mark is a hole in both. Two holes in different layers are the same mark when their centre, shape, size and angle are identical (TR-10). In a stack of three or more layers, no alignment mark is a hole in every layer. Dowel holes are the exception. | G-7 (#63) |
| TR-10 | A shared mark has identical coordinates in every layer that holds it. A new point within the snapping radius of a stored mark takes the stored coordinates. `--mark-tolerance` (`marks.tolerance`) is that radius. The default is 0.1 × mark size (proposed). When two stored marks are in range, the nearer one wins. | G-15 (#72), G-22 (#82) |

### Number

| ID | Requirement | Closes |
|---|---|---|
| TR-11 | Each piece carries its layer number, not the word "Slice". The number is the slice index, which starts at 0, as in the file name `slice_000.svg`. The number is drawn filled, so it engraves. It reads left to right along +x when the layer is viewed from above. It is drawn `--number-height` tall (`number.height`). The default is 5 mm (proposed). Its footprint lies wholly inside the piece, clear of the outline, holes and marks. The width is estimated conservatively as `number.width_factor` × height per character. The default factor is 0.6 (proposed). The font is `number.font_family`, default bold sans-serif. | G-18 (#75) |

### Checking and failure

| ID | Requirement | Closes |
|---|---|---|
| TR-12 | After slicing and before writing any file, the tool checks TR-2, TR-3 (the number fits) and TR-5 for every piece. If one fails, it writes nothing, prints to stderr the slice, the piece and the reason, and exits with code 1. `--allow-unaligned` (`checks.allow_unaligned`) turns these errors into warnings, writes the files and exits with 0. A short baseline (TR-4) is always a warning. | G-4 (#60) |

### Units and output

| ID | Requirement | Closes |
|---|---|---|
| TR-13 | `--units` sets the unit of the mesh and of every length option: layer height, target height, mark size, distances, tolerance and number height. The choices are `mm`, `cm` and `in`. The default is `mm`. Every SVG has the same `width` and `height`, given with that unit, and a `viewBox` in the same numbers. `--scale-factor` still rescales the mesh. | G-17 (#74) |
| TR-14 | Cut geometry (piece outlines and holes) is drawn in one colour, default red, with a stroke of `output.hairline_width` and no fill. The default width is a hairline of 0.01 mm, converted to the chosen unit. The number is drawn in black, filled, with no stroke. `--cut-color` and `--engrave-color` (`output.cut_color`, `output.engrave_color`) change the colours. `--mark-color` and the per-shape default colours are removed. The root `stroke-width` and `font-size` of the current output are removed. | G-23 (#83) |

### Dowel holes (later)

| ID | Requirement | Closes |
|---|---|---|
| TR-15 | A later version may mark some holes as dowel holes. A dowel hole has its own size, shape and fit clearance, and uses the `kerf` setting. It is not counted in TR-2, so dowels stay optional hardware. Nothing is built for this now. | Later |

### Settings

| ID | Requirement | Closes |
|---|---|---|
| TR-16 | Every number in TR-2 to TR-15 that depends on the machine, the material or judgment is a setting. Each has a default and a config-file key (see the table). The common ones also have a command-line option. A setting is taken from the command line first, then from the config file, then from its default. The config file is TOML. Its path is `--config`, or `layerforge.toml` in the current directory if that file exists. Lengths are in `--units`. Unknown keys, wrong types and out-of-range values stop the run before slicing, with exit code 2 and a message that names the file and the key. Status: #87 built the mechanism and the keys `layer_height`, `marks.size`, `marks.tolerance`, `marks.min_distance`, `marks.shapes` and `marks.angle`. Each later issue adds its own keys, and until then a key that is not built is an unknown key. | G-24 (#87, done) |

| Key | Option | Default | Basis | Used by |
|---|---|---|---|---|
| `units` | `--units` | `mm` | Convention | TR-13 |
| `layer_height` | `--layer-height` | 3.0 | Existing default. It is the sheet thickness. | TR-6 |
| `kerf` | `--kerf` | 0.3 mm | Proposed | TR-6, TR-15 |
| `marks.size` | `--mark-size` | larger of `min_hole_ratio` × layer height and `min_hole_kerf_factor` × kerf | Sourced | TR-6 |
| `marks.min_hole_ratio` | | 1 | Sourced (hole at least the thickness) | TR-6 |
| `marks.min_hole_kerf_factor` | | 1.5 | Sourced | TR-6 |
| `marks.min_distance` | `--mark-min-distance` | mark size | Sourced (centre one diameter from the edge) | TR-5 |
| `marks.min_web_ratio` | | 0.5 | Sourced (material between cuts at least half the thickness) | TR-5 |
| `marks.min_baseline_factor` | | 4 | Proposed | TR-4 |
| `marks.tolerance` | `--mark-tolerance` | 0.1 × mark size | Proposed | TR-10 |
| `marks.shapes` | `--available-shapes` | circle, square, triangle, arrow | Existing default | TR-8 |
| `marks.angle` | `--mark-angle` (degrees) | 0 | Existing default | TR-7 |
| `number.height` | `--number-height` | 5 mm | Proposed | TR-11 |
| `number.width_factor` | | 0.6 | Proposed | TR-11 |
| `number.font_family` | | bold sans-serif | Sourced | TR-11 |
| `output.cut_color` | `--cut-color` | red | Convention | TR-14 |
| `output.engrave_color` | `--engrave-color` | black | Convention | TR-14 |
| `output.hairline_width` | | 0.01 mm | Sourced | TR-14 |
| `checks.allow_unaligned` | `--allow-unaligned` | false | Decision | TR-12 |
| `checks.min_overlap_area` | | 0 | Decision. Any overlap counts. | TR-2 |

Defaults given in mm are converted to the chosen unit. A default that depends on another setting (for example the mark size) follows that setting.

Example `layerforge.toml` for a 3 mm sheet and a machine with a 0.25 mm kerf:

```toml
units = "mm"
layer_height = 3.0
kerf = 0.25

[marks]
size = 3.0
shapes = ["circle", "triangle", "square"]

[number]
height = 6.0
```

## Command line changes

| Option | Change |
|---|---|
| `--units` | New. Default `mm`. |
| `--config` | New (#87). Path to a TOML settings file (TR-16). |
| `--kerf` | New. Default 0.3 mm (proposed). |
| `--mark-size` | New (#87). Sets the size. Without it the size is still the FR-21 rule. The default from the sheet thickness and kerf (TR-6) comes with #62. |
| `--mark-min-distance` | Default changes from 10 to the mark size. It measures centre to outline. |
| `--mark-tolerance` | Now a snapping radius. Default 0.1 × mark size (proposed). |
| `--mark-angle` | Still degrees. 0 points along +x and turns counter-clockwise. |
| `--available-shapes` | Limits the shapes. It no longer sets the order. |
| `--number-height` | New. Default 5 units (proposed). |
| `--allow-unaligned` | New. Turns alignment errors into warnings. |
| `--cut-color`, `--engrave-color` | New. Replace `--mark-color`. |

The project is at version 0.1.0, so removing `--mark-color` and changing defaults is acceptable.

## Where the numbers come from

Search results from design guides gave these starting points. They are not measured on the owner's machine, and they vary with material and laser, so a test cut should confirm them.

| Value | Basis | Status |
|---|---|---|
| Hole size at least the material thickness, or at least 1.5 × kerf | [Laser design guides](https://kasulaser.com/how-small-can-a-laser-cutter-cut/) | Sourced |
| Centre at least one diameter from the edge | Same | Sourced |
| Material between two cuts at least half the thickness | Same | Sourced |
| CO₂ kerf about 0.25 to 0.5 mm | [SendCutSend](https://sendcutsend.com/blog/what-is-kerf-in-laser-cutting/) | Sourced |
| Hairline stroke for cuts, colour for the operation, text as outlines | [SVG preparation guide](https://www.svgvector.com/blog/svg-for-laser-cutting-guide.html), [text guide](https://text-to-svg.com/guide/convert-text-to-svg-for-laser-cutting) | Sourced |
| Text under about 5 mm needs a bold sans font. Strokes of 0.3 mm or more. | [The Laser Co](https://thelaserco.com/laser-engraving-font-sizes/) | Sourced |
| STL has no units. Millimetres is the convention. | [UnitFYI](https://unitfyi.com/blog/unit-conversions-for-3d-printing/) | Sourced |
| Through holes for dowels in stacked models | [Tulane makerspace](https://makerspace.tulane.edu/index.php/Creating_Stacked_3d_Models_using_the_Laser_Cutter) | Sourced |
| Warnings do not change the exit code. Errors do. | [Command Line Interface Guidelines](https://clig.dev/) | Sourced |
| Minimum baseline factor 4 | Judgment | Proposed |
| Snapping radius 0.1 × mark size | Judgment | Proposed |
| Number width factor 0.6 | Judgment | Proposed |
| Kerf 0.3 mm | Inside the range in the row above | Proposed |
| Default number height 5 | Source says under about 5 mm needs a bold font | Proposed |
| Angle 0 along +x, counter-clockwise | Geometry convention. shapely rotates +x by +90° to +y. | Checked |

## Assumptions to confirm

- The default text is a bold sans font written as `<text>`. Converting the number to outlines comes later.
- The default kerf of 0.3 mm is a proposal inside the sourced range of 0.25 to 0.5 mm.
- Cut numbers (`--number-mode cut`) are not built. The number is always drawn to engrave.
