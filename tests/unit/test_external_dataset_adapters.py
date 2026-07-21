"""Tests for Tier-A external dataset adapters."""

from __future__ import annotations

from nano_coder.infrastructure.external_dataset_adapters import (
    ensure_imperative_instruction,
    has_html_document_root,
    vulcan_record_to_synthetic,
    weba11y_record_to_synthetic,
)


def test_ensure_imperative_instruction_adds_write_prefix():
    assert ensure_imperative_instruction("a pet gallery page").startswith("Write ")


def test_vulcan_record_to_synthetic_maps_messages():
    row = {
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "Build a contact form with validation."},
            {"role": "assistant", "content": "<!DOCTYPE html><html><body><form></form></body></html>"},
        ]
    }
    record = vulcan_record_to_synthetic(row, serial=1, source_id="1")
    assert record is not None
    assert record["targetLanguage"] == "HTML"
    assert record["id"] == "syn-html-0001"
    assert "forms" in record["tags"] or "semantic" in record["tags"]


def test_weba11y_record_rejects_react():
    row = {
        "prompt": "Create a React dashboard with hooks.",
        "code": "<div>import React from 'react'</div>",
    }
    assert weba11y_record_to_synthetic(row, serial=2) is None


def test_weba11y_record_rejects_css_only_snippet():
    row = {
        "prompt": "Style a responsive card layout with CSS grid.",
        "code": ".card { display: grid; grid-template-columns: 1fr 1fr; }",
    }
    assert weba11y_record_to_synthetic(row, serial=3) is None


def test_has_html_document_root():
    assert has_html_document_root("<!DOCTYPE html><html><body></body></html>")
    assert not has_html_document_root(".wrapper { color: red; }")
