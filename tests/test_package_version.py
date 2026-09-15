from importlib.metadata import version

import tabito_itemgen


def test_package_version_matches_installed_metadata():
    assert tabito_itemgen.__version__ == version("tabito-common-test-chinese-itemgen")
