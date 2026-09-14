from __future__ import annotations

import tabito_itemgen.exam_ui as exam_ui
from tabito_itemgen.exam_preview import render_simple_section_preview
from tabito_itemgen.exam_ui_style import APP_CSS

# Keep the production workbench logic stable while replacing only presentation
# surfaces.  The browser preview shares semantics with the XeLaTeX booklet, and
# the app chrome is intentionally flat/editorial rather than dashboard-like.
exam_ui._preview_simple_section = render_simple_section_preview
exam_ui.APP_CSS = APP_CSS


def main() -> None:
    exam_ui.main()


if __name__ == "__main__":
    main()
