"""Integration tests via FastAPI TestClient — exercise every endpoint."""

from __future__ import annotations


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.text == "ok"


def test_api_projects_returns_list(client, make_project):
    make_project("alpha")
    make_project("beta")
    r = client.get("/api/projects")
    assert r.status_code == 200
    slugs = sorted(p["slug"] for p in r.json())
    assert slugs == ["alpha", "beta"]


def test_index_renders_with_tabs(client, make_project):
    make_project("alpha")
    r = client.get("/")
    assert r.status_code == 200
    assert "Comic Pipeline Dashboard" in r.text
    assert "alpha" in r.text


def test_index_with_no_projects_shows_empty_message(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "No projects discovered" in r.text


def test_widget_stages_renders(client, make_project):
    make_project("alpha", pages=1, panels_per_page=2, accepted={"p01-01"})
    r = client.get("/widgets/stages", params={"project": "alpha"})
    assert r.status_code == 200
    assert "Script breakdown" in r.text
    assert "Generation" in r.text
    assert "1/2 panels accepted" in r.text


def test_widget_panels_renders_grid(client, make_project):
    make_project("alpha", pages=2, panels_per_page=2)
    r = client.get("/widgets/panels", params={"project": "alpha"})
    assert r.status_code == 200
    assert r.text.count('<figure class="panel-tile') == 4
    assert "p01-01" in r.text
    assert "p02-02" in r.text


def test_widget_panel_versions_modal(client, make_project):
    make_project("alpha", pages=1, panels_per_page=1, accepted={"p01-01"})
    r = client.get(
        "/widgets/panel-versions", params={"project": "alpha", "folder": "p01-01"}
    )
    assert r.status_code == 200
    assert "accepted v1" in r.text
    assert "/image?project=alpha" in r.text


def test_widget_panel_versions_404_for_unknown_folder(client, make_project):
    make_project("alpha")
    r = client.get(
        "/widgets/panel-versions", params={"project": "alpha", "folder": "no-such"}
    )
    assert r.status_code == 404


def test_widget_findings_uses_run_rules_audit(
    client, make_project, server_module, monkeypatch
):
    make_project("alpha")
    monkeypatch.setattr(
        server_module,
        "run_rules_audit",
        lambda _root: {
            "findings": [
                {
                    "severity": "hard",
                    "message": "mocked hard",
                    "category": "test",
                    "page": 1,
                    "panel_id": "p01-01",
                    "suggestion": "fix it",
                },
                {
                    "severity": "soft",
                    "message": "mocked soft",
                    "category": "test",
                    "page": None,
                    "panel_id": None,
                    "suggestion": "",
                },
            ]
        },
    )
    r = client.get("/widgets/findings", params={"project": "alpha"})
    assert r.status_code == 200
    assert "mocked hard" in r.text
    assert "mocked soft" in r.text
    assert "1 hard" in r.text
    assert "1 soft" in r.text


def test_widget_findings_renders_error_banner(
    client, make_project, server_module, monkeypatch
):
    make_project("alpha")
    monkeypatch.setattr(
        server_module,
        "run_rules_audit",
        lambda _root: {"error": "subprocess died", "findings": []},
    )
    r = client.get("/widgets/findings", params={"project": "alpha"})
    assert r.status_code == 200
    assert "subprocess died" in r.text


def test_widget_next_panel_pending(client, make_project, server_module, monkeypatch):
    make_project("alpha")
    monkeypatch.setattr(
        server_module,
        "run_next_panel",
        lambda _root: {
            "project_root": "/x",
            "next_panel": {
                "panel_id": "p01-02",
                "page_number": 1,
                "camera": "wide",
                "characters": ["alice"],
                "location": "lab",
                "action": "Alice waves.",
            },
            "accepted_count": 3,
            "remaining_count": 7,
            "aspect": "3:4",
            "count": "x4",
            "refs_to_attach_in_order": [
                {
                    "kind": "face_card",
                    "character": "alice",
                    "path": "references/characters/alice/01.jpg",
                    "reason": "canonical face anchor",
                }
            ],
            "stage_change": False,
            "composed_prompt": "render this",
        },
    )
    r = client.get("/widgets/next-panel", params={"project": "alpha"})
    assert r.status_code == 200
    assert "p01-02" in r.text
    assert "Alice waves." in r.text
    assert "face_card" in r.text
    assert "3/10 accepted" in r.text


def test_widget_next_panel_caught_up(
    client, make_project, server_module, monkeypatch
):
    make_project("alpha")
    monkeypatch.setattr(
        server_module,
        "run_next_panel",
        lambda _root: {
            "next_panel": None,
            "message": "All shotlist panels have an accepted version.",
            "accepted_count": 20,
        },
    )
    r = client.get("/widgets/next-panel", params={"project": "alpha"})
    assert r.status_code == 200
    assert "caught up" in r.text
    assert "20 panels accepted" in r.text


def test_widget_next_panel_error(client, make_project, server_module, monkeypatch):
    make_project("alpha")
    monkeypatch.setattr(
        server_module, "run_next_panel", lambda _root: {"error": "kaboom"}
    )
    r = client.get("/widgets/next-panel", params={"project": "alpha"})
    assert r.status_code == 200
    assert "kaboom" in r.text


def test_unknown_project_returns_404(client):
    r = client.get("/widgets/stages", params={"project": "does-not-exist"})
    assert r.status_code == 404


def test_thumb_endpoint_returns_jpeg(client, make_project):
    make_project("alpha", pages=1, panels_per_page=1)
    r = client.get(
        "/thumb",
        params={"project": "alpha", "path": "pages/panels/p01-01/v1.png", "w": 96},
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/jpeg"
    assert r.content.startswith(b"\xff\xd8")  # JPEG magic


def test_image_endpoint_returns_file(client, make_project):
    make_project("alpha", pages=1, panels_per_page=1)
    r = client.get(
        "/image",
        params={"project": "alpha", "path": "pages/panels/p01-01/v1.png"},
    )
    assert r.status_code == 200
    assert r.content.startswith(b"\x89PNG")  # PNG magic


def test_image_rejects_path_traversal(client, make_project):
    make_project("alpha", pages=1, panels_per_page=1)
    r = client.get(
        "/image", params={"project": "alpha", "path": "../../etc/passwd"}
    )
    assert r.status_code == 400


def test_static_htmx_served(client):
    r = client.get("/static/htmx.min.js")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/javascript") or \
           r.headers["content-type"].startswith("application/javascript")
    assert len(r.content) > 1000
