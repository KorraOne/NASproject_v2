"""Samba share manifest tests."""

from pathlib import Path

from frogswork_api.integrations import samba_shares


def test_rebuild_manifest_lists_share_fragments(tmp_path, monkeypatch):
    staging = tmp_path / "staging"
    shares_d = tmp_path / "shares.d"
    staging.mkdir()
    shares_d.mkdir()
    (shares_d / "00-placeholder.conf").write_text("# placeholder\n", encoding="utf-8")
    (shares_d / "Projects.conf").write_text("[shared-Projects]\n", encoding="utf-8")

    monkeypatch.setattr(samba_shares, "SAMBA_SHARES_STAGING", staging)
    monkeypatch.setattr(samba_shares, "SAMBA_SHARES_D", shares_d)

    def fake_install(*args):
        dest = Path(args[-1])
        src = Path(args[-2])
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    monkeypatch.setattr(samba_shares, "run_cmd", fake_install)

    samba_shares.rebuild_manifest()

    manifest = shares_d / samba_shares.MANIFEST_FILENAME
    text = manifest.read_text(encoding="utf-8")
    assert "Projects.conf" in text
    assert "00-placeholder" not in text
    assert "00-manifest" not in text
