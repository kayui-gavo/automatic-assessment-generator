from __future__ import annotations

import tabito_itemgen.exam_ui as exam_ui
from tabito_itemgen.exam_preview import render_simple_section_preview

# Keep the large production workbench stable while replacing only the student/
# teacher surface renderer.  The same presentation semantics are shared with
# the XeLaTeX booklet through exam_surface.py.
exam_ui._preview_simple_section = render_simple_section_preview


def main() -> None:
    exam_ui.main()


if __name__ == "__main__":
    main()
