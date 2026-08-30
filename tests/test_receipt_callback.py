import os
import json
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from callbacks.receipt_callback import get_start_time_callback, get_receipt_callback


# ---------------------------------------------------------------------------
# Minimal mock helpers
# ---------------------------------------------------------------------------

def _make_part(text=None):
    p = SimpleNamespace(text=text)
    return p


def _make_content(role="user", texts=("hello",)):
    return SimpleNamespace(role=role, parts=[_make_part(t) for t in texts])


def _make_ctx(state=None, user_content=None):
    ctx = SimpleNamespace(
        state=dict(state or {}),
        user_content=user_content,
    )
    return ctx


def _make_llm_request(contents=None):
    return SimpleNamespace(contents=contents or [])


def _make_llm_response(content=None, partial=None):
    return SimpleNamespace(content=content, partial=partial)


# ---------------------------------------------------------------------------
# Unit tests — before_model_callback (get_start_time_callback)
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_start_time_callback_sets_state():
    callback = get_start_time_callback()
    ctx = _make_ctx()
    req = _make_llm_request()
    callback(ctx, req)
    assert "_run_start_time" in ctx.state
    assert isinstance(ctx.state["_run_start_time"], float)


@pytest.mark.unit
def test_start_time_callback_returns_none():
    callback = get_start_time_callback()
    ctx = _make_ctx()
    req = _make_llm_request()
    result = callback(ctx, req)
    assert result is None


# ---------------------------------------------------------------------------
# Unit tests — after_model_callback (get_receipt_callback)
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_receipt_callback_skips_partial_response():
    """Streaming chunks (partial=True) must not trigger receipt creation."""
    callback = get_receipt_callback("test_agent", "gemini-2.5-flash")
    ctx = _make_ctx(state={"_run_start_time": 0.0}, user_content=_make_content())
    resp = _make_llm_response(content=_make_content(role="model", texts=("hi",)), partial=True)

    with patch("callbacks.receipt_callback.create_receipt") as mock_create:
        callback(ctx, resp)
        mock_create.assert_not_called()


@pytest.mark.unit
def test_receipt_callback_returns_none(sample_receipt):
    callback = get_receipt_callback("test_agent", "gemini-2.5-flash")
    ctx = _make_ctx(state={"_run_start_time": 0.0}, user_content=_make_content())
    resp = _make_llm_response(content=_make_content(role="model", texts=("answer",)), partial=None)

    with patch("callbacks.receipt_callback.create_receipt", return_value=sample_receipt), \
         patch("callbacks.receipt_callback.format_receipt", return_value="---"), \
         patch("callbacks.receipt_callback.save_receipt_to_file"):
        result = callback(ctx, resp)

    assert result is None


@pytest.mark.unit
def test_receipt_callback_handles_no_user_content(sample_receipt):
    """If ctx.user_content is None, callback should not raise."""
    callback = get_receipt_callback("test_agent", "gemini-2.5-flash")
    ctx = _make_ctx(state={"_run_start_time": 0.0}, user_content=None)
    resp = _make_llm_response(content=_make_content(role="model", texts=("hi",)), partial=None)

    with patch("callbacks.receipt_callback.create_receipt", return_value=sample_receipt), \
         patch("callbacks.receipt_callback.format_receipt", return_value="---"), \
         patch("callbacks.receipt_callback.save_receipt_to_file"):
        result = callback(ctx, resp)

    assert result is None


@pytest.mark.unit
def test_receipt_callback_writes_file(tmp_path, sample_receipt):
    """Callback must create the directory and write a JSONL line."""
    receipt_dir = str(tmp_path / "logs" / "receipts")

    callback = get_receipt_callback("test_agent", "gemini-2.5-flash")
    ctx = _make_ctx(state={"_run_start_time": 0.0}, user_content=_make_content())
    resp = _make_llm_response(content=_make_content(role="model", texts=("answer",)), partial=None)

    with patch("callbacks.receipt_callback.create_receipt", return_value=sample_receipt), \
         patch("callbacks.receipt_callback.format_receipt", return_value="---"), \
         patch("callbacks.receipt_callback._RECEIPT_DIR", receipt_dir):
        callback(ctx, resp)

    filepath = os.path.join(receipt_dir, "test_agent.jsonl")
    assert os.path.exists(filepath)
    with open(filepath) as f:
        data = json.loads(f.read().strip())
    assert data["agent_name"] == "test_agent"
