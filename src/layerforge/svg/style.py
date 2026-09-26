"""How the SVG of a slice is drawn for a laser (TR-14)."""

from dataclasses import dataclass

from layerforge.units import from_mm

# A hairline: the widest stroke that the drivers of Epilog, Trotec and Universal lasers still
# read as a cut (TR-17). It is millimetres here, and :meth:`SVGStyle.for_units` converts it.
HAIRLINE_MM = 0.01
# The number is engraved, so it must be tall enough to read and to engrave (TR-11). Proposed, and
# the person can change it. Millimetres here, converted by :meth:`SVGStyle.for_units`.
NUMBER_HEIGHT_MM = 5.0
# The width of a character of a bold sans font is about 0.6 of its height; this is an estimate.
NUMBER_WIDTH_FACTOR = 0.6


@dataclass(frozen=True)
class SVGStyle:
    """The colours and the stroke of one SVG.

    Attributes
    ----------
    cut_color : str
        The stroke of everything that is cut: the outlines of a piece and the holes of the marks.
    engrave_color : str
        The fill of the number, which is engraved. It has no stroke.
    hairline_width : float
        The stroke width of every cut, in the unit of the run. ``SVGStyle()`` states it in
        millimetres. Use :meth:`for_units` for another unit.
    number_height : float
        The height of the number, in the unit of the run. It is also the font size.
    number_width_factor : float
        The estimated width of one character, as a multiple of the height.
    number_clearance : float
        The material between the number and every cut, in the unit of the run. The command sets
        it to the kerf, so the engraving keeps clear of the burn of the cut.
    """

    cut_color: str = "red"
    engrave_color: str = "black"
    hairline_width: float = HAIRLINE_MM
    number_height: float = NUMBER_HEIGHT_MM
    number_width_factor: float = NUMBER_WIDTH_FACTOR
    number_clearance: float = 0.0

    @classmethod
    def for_units(cls, units: str) -> "SVGStyle":
        """Return the default style with the hairline and the number height stated in ``units``."""
        return cls(
            hairline_width=from_mm(units, HAIRLINE_MM),
            number_height=from_mm(units, NUMBER_HEIGHT_MM),
        )
