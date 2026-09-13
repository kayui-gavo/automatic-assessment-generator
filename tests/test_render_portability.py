from __future__ import annotations

import subprocess

import pytest

from tabito_itemgen import render


def test_font_setup_uses_portable_latin_fallback_chain():
    setup = render._font_setup()

    assert "TeX Gyre Termes" in setup
    assert "Liberation Serif" in setup
    assert r"\IfFontExistsTF{Times New Roman}" in setup
    assert "Latin Modern Roman" in setup
    assert setup.index("Liberation Serif") < setup.index("Times New Roman")


def test_font_setup_does_not_require_a_dedicated_sc_font():
    setup = render._font_setup()

    assert "Noto Serif CJK SC" in setup
    assert "Songti SC" in setup
    assert r"\newcommand{\zhfont}{}" in setup


def test_compile_xelatex_surfaces_log_tail(monkeypatch, tmp_path):
    tex = tmp_path / "broken.tex"
    tex.write_text("broken", encoding="utf-8")
    output = "\n".join(f"line-{index}" for index in range(100))

    monkeypatch.setattr(render.shutil, "which", lambda _: "/usr/bin/xelatex")
    monkeypatch.setattr(
        render.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args=args[0], returncode=1, stdout=output),
    )

    with pytest.raises(RuntimeError) as exc_info:
        render.compile_xelatex(tex)

    message = str(exc_info.value)
    assert "broken.tex" in message
    assert "line-99" in message
    assert "line-20" in message
    assert "line-19" not in message
