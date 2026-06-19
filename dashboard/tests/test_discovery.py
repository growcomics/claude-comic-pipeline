"""Tests for project discovery, slugify, and config loading."""

from __future__ import annotations

from pathlib import Path


def test_slugify_basic(server_module):
    assert server_module._slugify("Chun-Li Iron Discipline") == "chun-li-iron-discipline"
    assert server_module._slugify("supergirl_overcharged") == "supergirl_overcharged"
    assert server_module._slugify("!!!---weird name") == "weird-name"
    assert server_module._slugify("") == "unnamed"


def test_load_config_reads_file(server_module, tmp_path, monkeypatch):
    cfg = tmp_path / "c.toml"
    cfg.write_text('project_globs = ["/x/*", "/y/*"]\n')
    monkeypatch.setattr(server_module, "CONFIG_PATH", cfg)
    out = server_module.load_config()
    assert out == {"project_globs": ["/x/*", "/y/*"]}


def test_load_config_returns_defaults_when_missing(server_module, tmp_path, monkeypatch):
    monkeypatch.setattr(server_module, "CONFIG_PATH", tmp_path / "nope.toml")
    out = server_module.load_config()
    assert "project_globs" in out
    assert len(out["project_globs"]) >= 1


def test_discover_projects_finds_projects(make_project, server_module):
    make_project("alpha")
    make_project("beta")
    out = server_module.discover_projects()
    slugs = sorted(p["slug"] for p in out)
    assert slugs == ["alpha", "beta"]


def test_discover_projects_skips_dirs_without_shotlist(
    make_project, projects_root, server_module
):
    make_project("has-shotlist")
    (projects_root / "no-shotlist").mkdir()
    out = server_module.discover_projects()
    slugs = [p["slug"] for p in out]
    assert "has-shotlist" in slugs
    assert "no-shotlist" not in slugs


def test_discover_projects_uses_shotlist_project_field_as_title(
    make_project, server_module
):
    make_project("the-slug", project_field="The Pretty Title")
    out = server_module.discover_projects()
    assert out[0]["slug"] == "the-slug"
    assert out[0]["title"] == "The Pretty Title"


def test_discover_projects_dedup_by_slug(make_project, server_module):
    # Same slug emerging from two configured globs should appear once.
    make_project("only-one")
    out = server_module.discover_projects()
    assert sum(1 for p in out if p["slug"] == "only-one") == 1


def test_resolve_project_404_for_unknown(server_module):
    from fastapi import HTTPException

    try:
        server_module.resolve_project("does-not-exist")
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        raise AssertionError("expected HTTPException")
