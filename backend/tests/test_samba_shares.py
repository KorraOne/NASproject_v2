"""Samba share helpers tests."""

from frogswork_api.integrations import samba_shares


def test_share_name_is_unified():
    assert samba_shares.share_name("Projects") == "frogswork"
    assert samba_shares.share_name() == "frogswork"
