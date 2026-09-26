"""How the SVG of a slice is drawn for a laser (TR-14)."""

from dataclasses import dataclass

from layerforge.units import from_mm

# A hairline: the widest stroke that the drivers of Epilog, Trotec and Universal lasers still
# read as a cut (TR-17). It is millimetres here, and :meth:`SVGStyle.for_units` converts it.
HAIRLINE_MM = 0.01


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
    """

    cut_color: str = "red"
    engrave_color: str = "black"
    hairline_width: float = HAIRLINE_MM

    @classmethod
    def for_units(cls, units: str) -> "SVGStyle":
        """Return the default style with the hairline stated in ``units``."""
        return cls(hairline_width=from_mm(units, HAIRLINE_MM))
