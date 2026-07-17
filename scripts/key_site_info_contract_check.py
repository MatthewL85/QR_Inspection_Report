"""Verify Key Site Information rich-content and UI contracts."""

from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


TEMPLATE_CONTRACTS = {
    "app/templates/super_admin/client/view_client.html": [
        "client-key-site-tablist",
        "data-key-site-tab",
        "data-key-site-panel",
        "Add Key Site Tab",
        "Edit Key Site Tab",
        "js-key-site-wysiwyg",
        "key_site_content",
        "forecolor backcolor",
        "image media",
        "tinymce.triggerSave",
    ],
    "app/templates/clients/key_info/list.html": [
        "Back to Key Site Info",
        "modal-dialog-scrollable",
        "key-info-proposal-modal",
        "key_site_content",
        "js-wysiwyg",
        "forecolor backcolor",
        "image media",
        "tinymce.triggerSave",
    ],
}


def _check_template_contracts(failures: list[str]) -> None:
    for relative_path, tokens in TEMPLATE_CONTRACTS.items():
        template_path = PROJECT_ROOT / relative_path
        if not template_path.exists():
            failures.append(f"Template missing: {relative_path}")
            continue
        content = template_path.read_text(encoding="utf-8")
        for token in tokens:
            if token not in content:
                failures.append(f"{relative_path} is missing Key Site token: {token}")

        if "|safe" in content and "key_site_content" in content:
            unsafe_key_site_lines = [
                line.strip()
                for line in content.splitlines()
                if "|safe" in line and ("s.content" in line or "proposed_content" in line or "section.content" in line)
            ]
            if unsafe_key_site_lines:
                failures.append(
                    f"{relative_path} renders Key Site content with |safe instead of key_site_content: "
                    + " | ".join(unsafe_key_site_lines[:2])
                )

        if relative_path.endswith("clients/key_info/list.html") and "Propose Update — {{ s.title }}" in content:
            failures.append("Advanced Key Site modal still contains the duplicate legacy proposal title.")


def _check_rich_content_filter(failures: list[str]) -> None:
    from app import create_app

    app = create_app()
    with app.app_context():
        renderer = app.jinja_env.filters.get("key_site_content")
        if not renderer:
            failures.append("key_site_content Jinja filter is not registered.")
            return

        raw = """
        <p style="color: rgb(224, 62, 45); text-align: center;" onclick="alert(1)">Gate code updated</p>
        <ul><li><strong>Call contractor before arrival</strong></li></ul>
        <a href="javascript:alert(1)">Bad link</a>
        <a href="https://example.invalid/access">Safe link</a>
        <video controls width="300" height="150"><source src="/static/uploads/key_info/12/demo.mp4" type="video/mp4"></video>
        <script>alert("bad")</script>
        """
        rendered = str(renderer(raw))

        expected_present = [
            'style="color: rgb(224, 62, 45); text-align: center"',
            "<ul>",
            "<li>",
            "<strong>Call contractor before arrival</strong>",
            'href="https://example.invalid/access"',
            'target="_blank"',
            "<video controls",
            'src="/static/uploads/key_info/12/demo.mp4"',
        ]
        for token in expected_present:
            if token not in rendered:
                failures.append(f"key_site_content did not preserve expected safe formatting: {token}")

        forbidden = ["onclick", "javascript:", "<script", "alert(&quot;bad&quot;)"]
        for token in forbidden:
            if token in rendered:
                failures.append(f"key_site_content allowed unsafe content: {token}")

        plain = str(renderer("Line one\nLine two"))
        if "<p>Line one</p>" not in plain or "<p>Line two</p>" not in plain:
            failures.append("key_site_content should convert plain line breaks into paragraphs.")


def main() -> int:
    failures: list[str] = []
    _check_template_contracts(failures)
    _check_rich_content_filter(failures)

    if failures:
        print("FAILED: Key Site Information contract failed")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("PASSED: Key Site Information rich-content contract is stable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
