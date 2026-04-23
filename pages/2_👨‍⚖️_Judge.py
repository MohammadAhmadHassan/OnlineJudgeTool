"""
Judge Dashboard - Queue based review workflow
Each solved submission appears as a queue entry that moves through:
pending_review -> under_review -> reviewed
"""
import os
import sys
import uuid
import json
import importlib
from datetime import datetime

import pandas as pd
import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_manager import create_data_manager


st.set_page_config(
    page_title="Judge Review Queue",
    page_icon="👨‍⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown(
    """
<style>
    .metric-card {
        border: 1px solid #e6e6e6;
        border-radius: 12px;
        padding: 1rem;
        background: #ffffff;
    }
    .status-chip {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 0.4rem;
    }
    .status-pending { background: #fff4d9; color: #8a5a00; }
    .status-under-review { background: #dff2ff; color: #0e4f7a; }
    .status-reviewed { background: #e7f8e8; color: #1b5d28; }
    .status-approved { background: #d8f5db; color: #125a20; }
    .status-rejected { background: #ffe0e0; color: #7a1f1f; }
    .panel {
        border: 1px solid #ececec;
        border-radius: 12px;
        padding: 1rem;
        background: #fafafa;
    }
</style>
""",
    unsafe_allow_html=True,
)


STATUS_ORDER = {
    "pending_review": 0,
    "under_review": 1,
    "reviewed": 2,
}

STATUS_LABEL = {
    "pending_review": "Pending Review",
    "under_review": "Under Review",
    "reviewed": "Reviewed",
}


@st.cache_resource
def get_data_manager():
    return create_data_manager()


data_manager = get_data_manager()


def ensure_judge_session():
    if "judge_session_id" not in st.session_state:
        st.session_state.judge_session_id = str(uuid.uuid4())[:8]
    if "judge_name" not in st.session_state:
        st.session_state.judge_name = f"Judge-{st.session_state.judge_session_id}"
    if "judge_auto_refresh_enabled" not in st.session_state:
        st.session_state.judge_auto_refresh_enabled = True
    if "judge_refresh_interval_seconds" not in st.session_state:
        st.session_state.judge_refresh_interval_seconds = 5


ensure_judge_session()


def parse_timestamp(value):
    if not value:
        return None
    text = str(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None


def format_timestamp(value):
    parsed = parse_timestamp(value)
    if not parsed:
        return "-"
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def normalize_review_status(problem_data):
    explicit = problem_data.get("review_status")
    if explicit in ("pending_review", "under_review", "reviewed"):
        return explicit

    approval = problem_data.get("judge_approval")
    if approval in ("approved", "rejected"):
        return "reviewed"

    best = problem_data.get("best_result", {})
    if best and best.get("all_passed", False):
        return "pending_review"

    return "not_ready"


def normalize_queue_entries(raw_entries):
    entries = []
    for entry in raw_entries:
        competitor = entry.get("competitor")
        problem_id = entry.get("problem_id")
        if competitor is None or problem_id is None:
            continue

        review_status = entry.get("review_status", "pending_review")
        if review_status not in STATUS_ORDER:
            review_status = "pending_review"

        judge_approval = entry.get("judge_approval") or "pending"
        locked_by = entry.get("locked_by")

        entries.append({
            "entry_key": f"{competitor}::{problem_id}",
            "competitor": competitor,
            "problem_id": problem_id,
            "review_status": review_status,
            "judge_approval": judge_approval,
            "locked_by": locked_by,
            "locked_at": entry.get("locked_at"),
            "reviewed_at": entry.get("reviewed_at"),
            "submitted_at": entry.get("submitted_at"),
            "attempts": int(entry.get("attempts", 0) or 0),
            "passed_tests": int(entry.get("passed_tests", 0) or 0),
            "total_tests": int(entry.get("total_tests", 0) or 0),
            "level": entry.get("level"),
            "week": entry.get("week"),
        })

    def submitted_epoch(item):
        parsed = parse_timestamp(item.get("submitted_at"))
        if not parsed:
            return 0.0
        try:
            return parsed.timestamp()
        except Exception:
            return 0.0

    # Keep queue order stable to avoid row-index drift after status changes.
    entries.sort(key=lambda item: (-submitted_epoch(item), str(item.get("entry_key"))))
    return entries


def get_review_queue_entries():
    if hasattr(data_manager, "get_review_queue"):
        raw_entries = data_manager.get_review_queue()
    else:
        raw_entries = []
    return normalize_queue_entries(raw_entries)


def get_streamlit_autorefresh_fn():
    """Dynamically load streamlit-autorefresh if installed."""
    try:
        module = importlib.import_module("streamlit_autorefresh")
        return getattr(module, "st_autorefresh", None)
    except Exception:
        return None


def invalidate_queue_cache():
    st.session_state.pop("judge_queue_cache_entries", None)
    st.session_state.pop("judge_queue_cache_version", None)


def get_queue_entries_with_version_cache():
    """Reuse queue entries when backend data version is unchanged."""
    version_token = None
    if hasattr(data_manager, "get_data_version"):
        try:
            version_token = data_manager.get_data_version()
        except Exception:
            version_token = None

    if version_token is not None:
        cached_version = st.session_state.get("judge_queue_cache_version")
        cached_entries = st.session_state.get("judge_queue_cache_entries")
        if cached_entries is not None and cached_version == version_token:
            return cached_entries

    entries = get_review_queue_entries()
    st.session_state.judge_queue_cache_entries = entries
    st.session_state.judge_queue_cache_version = version_token
    return entries


def get_selected_rows_from_table_event(table_event):
    """Read selected rows only from the current dataframe selection event."""
    try:
        return list(table_event.selection.rows)
    except Exception:
        return []


def get_selected_rows_from_table_state(widget_key):
    """Read selected rows from persisted widget state (no new selection event)."""
    table_state = st.session_state.get(widget_key)
    if table_state is None:
        return []

    if isinstance(table_state, dict):
        selection_state = table_state.get("selection", {})
        rows = selection_state.get("rows", []) or []
        try:
            return list(rows)
        except Exception:
            return []

    try:
        return list(table_state.selection.rows)
    except Exception:
        return []


def split_entry_key(entry_key):
    if not entry_key or "::" not in str(entry_key):
        return None, None

    competitor_name, raw_problem_id = str(entry_key).split("::", 1)
    if str(raw_problem_id).isdigit():
        return competitor_name, int(raw_problem_id)
    return competitor_name, raw_problem_id


def entry_widget_key(prefix, entry_key):
    token = str(entry_key).replace("::", "__").replace(" ", "_")
    return f"{prefix}_{token}"


def parse_optional_int(value):
    if value in (None, "", "All"):
        return None
    try:
        return int(value)
    except Exception:
        return None


@st.cache_data(ttl=3600)
def get_problem_definition(problem_id, week=None, level=None):
    """Load problem metadata (title/description) for judge context."""
    problem_key = str(problem_id)
    week_int = parse_optional_int(week)
    level_int = parse_optional_int(level)
    lookup_problem_id = int(problem_key) if problem_key.isdigit() else problem_id

    # Try direct lookup first.
    try:
        problem = data_manager.get_problem_by_id(lookup_problem_id, week=week_int)
        if isinstance(problem, dict) and problem:
            return problem
    except Exception:
        pass

    # Fall back to indexed problem list lookup.
    try:
        problems = data_manager.get_problems(week=week_int, level=level_int)
        if isinstance(problems, dict):
            for candidate_id, payload in problems.items():
                if str(candidate_id) == problem_key and isinstance(payload, dict):
                    return payload
    except Exception:
        pass

    # Final fallback for local JSON deployments without backend problem APIs.
    workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    problems_dir = os.path.join(workspace_root, "problems")
    candidate_files = []
    if problem_key.isdigit():
        candidate_files = [
            f"problem{int(problem_key)}.json",
            f"harder_problem_{int(problem_key)}.json",
        ]
    else:
        candidate_files = [f"{problem_key}.json"]

    for file_name in candidate_files:
        file_path = os.path.join(problems_dir, file_name)
        if not os.path.exists(file_path):
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                return payload
        except Exception:
            continue

    return None


def get_problem_payload(competitor_name, problem_id):
    competitor_data = data_manager.get_competitor_data(competitor_name)
    if not competitor_data:
        return None, None, [], {}

    problems = competitor_data.get("problems", {})
    problem_data = problems.get(str(problem_id))

    if problem_data is None:
        # Fallback if incoming key type does not match storage key type.
        for stored_problem_id, payload in problems.items():
            if str(stored_problem_id) == str(problem_id):
                problem_data = payload
                break

    if not problem_data:
        return competitor_data, None, [], {}

    submissions = problem_data.get("submissions", [])
    latest = submissions[-1] if submissions else {}
    return competitor_data, problem_data, submissions, latest


def invalidate_problem_payload_cache(entry_key=None):
    cache = st.session_state.get("judge_problem_payload_cache")
    if not isinstance(cache, dict):
        st.session_state.pop("judge_problem_payload_cache", None)
        return

    if entry_key is None:
        st.session_state.pop("judge_problem_payload_cache", None)
        return

    cache.pop(str(entry_key), None)
    if cache:
        st.session_state.judge_problem_payload_cache = cache
    else:
        st.session_state.pop("judge_problem_payload_cache", None)


def get_problem_payload_cached(competitor_name, problem_id):
    """Get selected problem payload with backend-version-aware caching."""
    entry_key = f"{competitor_name}::{problem_id}"
    version_token = None
    if hasattr(data_manager, "get_data_version"):
        try:
            version_token = data_manager.get_data_version()
        except Exception:
            version_token = None

    if version_token is None:
        return get_problem_payload(competitor_name, problem_id)

    cache = st.session_state.get("judge_problem_payload_cache")
    if isinstance(cache, dict):
        cached_payload = cache.get(entry_key)
        if isinstance(cached_payload, dict) and cached_payload.get("version") == version_token:
            return cached_payload.get("payload", (None, None, [], {}))
    else:
        cache = {}

    payload = get_problem_payload(competitor_name, problem_id)
    cache[entry_key] = {
        "version": version_token,
        "payload": payload,
    }
    st.session_state.judge_problem_payload_cache = cache
    return payload


def to_write_problem_id(problem_id):
    text = str(problem_id)
    return int(text) if text.isdigit() else problem_id


def render_status_chip(status):
    label = STATUS_LABEL.get(status, status.replace("_", " ").title())
    css_class = {
        "pending_review": "status-pending",
        "under_review": "status-under-review",
        "reviewed": "status-reviewed",
    }.get(status, "status-pending")
    return f'<span class="status-chip {css_class}">{label}</span>'


def render_approval_chip(approval):
    if approval == "approved":
        return '<span class="status-chip status-approved">Approved</span>'
    if approval == "rejected":
        return '<span class="status-chip status-rejected">Rejected</span>'
    return '<span class="status-chip status-pending">Pending Decision</span>'


queue_entries = get_queue_entries_with_version_cache()


with st.sidebar:
    st.markdown("### Judge Session")
    judge_name_input = st.text_input(
        "Judge Name",
        value=st.session_state.judge_name,
        help="Used for review locking across multiple judges"
    ).strip()
    if judge_name_input:
        st.session_state.judge_name = judge_name_input

    st.caption(f"Session ID: {st.session_state.judge_session_id}")

    auto_refresh = st.toggle(
        "Auto-refresh queue",
        key="judge_auto_refresh_enabled",
        help="Refresh queue and lock states without leaving your current review"
    )
    refresh_interval_seconds = st.slider(
        "Refresh interval (seconds)",
        min_value=2,
        max_value=240,
        key="judge_refresh_interval_seconds"
    )
    if st.button("Refresh now", use_container_width=True):
        invalidate_queue_cache()
        invalidate_problem_payload_cache()
        st.rerun()

    st.markdown("---")
    st.markdown("### Filters")

    status_options = ["Pending Review", "Under Review", "Reviewed"]
    selected_status_labels = st.multiselect(
        "Queue Status",
        options=status_options,
        default=status_options,
    )

    selected_statuses = {
        "Pending Review": "pending_review",
        "Under Review": "under_review",
        "Reviewed": "reviewed",
    }
    status_filter_set = {
        selected_statuses[label]
        for label in selected_status_labels
        if label in selected_statuses
    }

    level_filter = st.selectbox(
        "Level",
        options=["All", 1, 2, 3, 4, 5],
        index=0,
    )
    week_filter = st.selectbox(
        "Week",
        options=["All", 1, 2, 3, 4, 5, 6, 7, 8],
        index=0,
    )

    locked_by_names = sorted({
        entry.get("locked_by")
        for entry in queue_entries
        if entry.get("locked_by")
    })
    locked_by_filter = st.selectbox(
        "Locked By",
        options=["All", "Unlocked", "Locked (Any)", "Locked By Me"] + locked_by_names,
        index=0,
    )

    search_query = st.text_input("Search Student / Problem", "").strip().lower()

    st.markdown("---")
    if st.button("Reset Competition", use_container_width=True):
        if st.session_state.get("confirm_reset"):
            data_manager.reset_competition()
            st.success("Competition reset complete")
            st.session_state.confirm_reset = False
            invalidate_queue_cache()
            invalidate_problem_payload_cache()
            st.rerun()
        else:
            st.session_state.confirm_reset = True
            st.warning("Click again to confirm reset")

if auto_refresh:
    st_autorefresh_fn = get_streamlit_autorefresh_fn()
    if st_autorefresh_fn is not None:
        st_autorefresh_fn(interval=int(refresh_interval_seconds) * 1000, key="judge_auto_refresh")
    else:
        st.caption(
            "Auto-refresh helper is unavailable in this runtime. "
            "Use 'Refresh now' for instant updates."
        )


st.title("Judge Review Queue")
st.caption(
    "Submitted solutions appear in this queue with status Pending Review. "
    "Opening one moves it to Under Review and locks it to the active judge."
)

pending_count = sum(1 for entry in queue_entries if entry["review_status"] == "pending_review")
under_review_count = sum(1 for entry in queue_entries if entry["review_status"] == "under_review")
reviewed_count = sum(1 for entry in queue_entries if entry["review_status"] == "reviewed")

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
metric_col1.metric("Queue Entries", len(queue_entries))
metric_col2.metric("Pending Review", pending_count)
metric_col3.metric("Under Review", under_review_count)
metric_col4.metric("Reviewed", reviewed_count)

filtered_entries = []
for entry in queue_entries:
    if status_filter_set and entry["review_status"] not in status_filter_set:
        continue

    entry_lock_owner = entry.get("locked_by")
    if locked_by_filter == "Unlocked" and entry_lock_owner:
        continue
    if locked_by_filter == "Locked (Any)" and not entry_lock_owner:
        continue
    if locked_by_filter == "Locked By Me" and entry_lock_owner != st.session_state.judge_name:
        continue
    if (
        locked_by_filter not in ["All", "Unlocked", "Locked (Any)", "Locked By Me"]
        and entry_lock_owner != locked_by_filter
    ):
        continue

    if level_filter != "All" and entry.get("level") != level_filter:
        continue

    if week_filter != "All" and entry.get("week") != week_filter:
        continue

    if search_query:
        haystack = f"{entry['competitor']} {entry['problem_id']}".lower()
        if search_query not in haystack:
            continue

    filtered_entries.append(entry)

st.markdown("---")

left_col, right_col = st.columns([2.2, 2.8])

with left_col:
    st.subheader("Submission Queue")
    freeze_table_selection = bool(st.session_state.pop("freeze_table_selection_once", False))

    if not filtered_entries:
        st.info("No queue entries match the current filters.")
    else:
        table_rows = []
        for entry in filtered_entries:
            table_rows.append({
                "Student": entry["competitor"],
                "Problem": f"Problem {entry['problem_id']}",
                "Status": STATUS_LABEL.get(entry["review_status"], entry["review_status"]),
                "Decision": entry["judge_approval"].capitalize(),
                "Locked By": entry.get("locked_by") or "-",
                "Submitted": format_timestamp(entry.get("submitted_at")),
                "Tests": f"{entry['passed_tests']}/{entry['total_tests']}",
                "Attempts": entry["attempts"],
            })

        queue_df = pd.DataFrame(table_rows)
        selection = st.dataframe(
            queue_df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="review_queue_table",
        )

        event_rows = get_selected_rows_from_table_event(selection)
        if event_rows and not freeze_table_selection:
            selected_index = event_rows[0]
            if 0 <= selected_index < len(filtered_entries):
                st.session_state.selected_review_entry = filtered_entries[selected_index]["entry_key"]
        elif "selected_review_entry" not in st.session_state and filtered_entries:
            persisted_rows = get_selected_rows_from_table_state("review_queue_table")
            if persisted_rows:
                selected_index = persisted_rows[0]
                if 0 <= selected_index < len(filtered_entries):
                    st.session_state.selected_review_entry = filtered_entries[selected_index]["entry_key"]
                else:
                    st.session_state.selected_review_entry = filtered_entries[0]["entry_key"]
            else:
                st.session_state.selected_review_entry = filtered_entries[0]["entry_key"]

with right_col:
    st.subheader("Review Panel")

    judge_name = st.session_state.judge_name
    active_review_entry = st.session_state.get("active_review_entry")
    if active_review_entry:
        selected_key = active_review_entry
        st.session_state.selected_review_entry = active_review_entry
    else:
        selected_key = st.session_state.get("selected_review_entry")

    selected_entry = None
    if selected_key:
        selected_entry = next((item for item in queue_entries if item["entry_key"] == selected_key), None)

    if not selected_entry and selected_key:
        fallback_competitor, fallback_problem_id = split_entry_key(selected_key)
        if fallback_competitor is not None and fallback_problem_id is not None:
            selected_entry = {
                "entry_key": selected_key,
                "competitor": fallback_competitor,
                "problem_id": fallback_problem_id,
                "review_status": "under_review" if st.session_state.get("active_review_entry") == selected_key else "pending_review",
                "judge_approval": "pending",
                "locked_by": judge_name if st.session_state.get("active_review_entry") == selected_key else None,
                "locked_at": None,
                "reviewed_at": None,
                "submitted_at": None,
                "attempts": 0,
                "passed_tests": 0,
                "total_tests": 0,
                "level": None,
                "week": None,
            }

    if not selected_entry:
        st.info("Select a queue entry to review.")
    else:
        competitor_name = selected_entry["competitor"]
        problem_id = selected_entry["problem_id"]
        entry_key = selected_entry["entry_key"]

        current_status = selected_entry.get("review_status", "pending_review")
        current_approval = selected_entry.get("judge_approval", "pending")
        lock_owner = selected_entry.get("locked_by")
        if active_review_entry == entry_key:
            current_status = "under_review" if current_status == "pending_review" else current_status
            lock_owner = lock_owner or judge_name

        _, problem_data, submissions, latest_submission = get_problem_payload_cached(competitor_name, problem_id)
        if not problem_data:
            st.warning("Live submission details are temporarily unavailable. Auto-refresh will retry.")
            st.stop()

        live_status = normalize_review_status(problem_data)
        if STATUS_ORDER.get(current_status, -1) > STATUS_ORDER.get(live_status, -1):
            live_status = current_status
        current_status = live_status

        current_approval = problem_data.get("judge_approval", current_approval)
        lock_owner = problem_data.get("review_locked_by") or lock_owner

        problem_definition = get_problem_definition(
            problem_id,
            week=selected_entry.get("week"),
            level=selected_entry.get("level"),
        )

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(f"### {competitor_name} - Problem {problem_id}")
        st.markdown(
            f"{render_status_chip(current_status)} {render_approval_chip(current_approval)}",
            unsafe_allow_html=True,
        )

        with st.expander("Question Text", expanded=True):
            if problem_definition:
                question_title = problem_definition.get("title") or f"Problem {problem_id}"
                question_description = (
                    problem_definition.get("description")
                    or problem_definition.get("problem_statement")
                    or problem_definition.get("statement")
                    or "No question text available."
                )
                question_difficulty = problem_definition.get("difficulty")

                st.markdown(f"**Title:** {question_title}")
                if question_difficulty:
                    st.markdown(f"**Difficulty:** {question_difficulty}")
                st.markdown(question_description)
            else:
                st.caption("Question text could not be loaded for this problem.")

        meta_col1, meta_col2, meta_col3 = st.columns(3)
        meta_col1.markdown(f"**Locked By:** {lock_owner or '-'}")
        meta_col2.markdown(f"**Submitted:** {format_timestamp(latest_submission.get('submitted_at', latest_submission.get('timestamp')))}")
        meta_col3.markdown(f"**Tests Passed:** {latest_submission.get('passed_tests', latest_submission.get('tests_passed', 0))}/{latest_submission.get('total_tests', 0)}")

        can_open = current_status == "pending_review"
        mine_under_review = current_status == "under_review" and (
            lock_owner == judge_name or active_review_entry == entry_key
        )
        locked_by_other = (
            current_status == "under_review"
            and lock_owner
            and lock_owner != judge_name
            and active_review_entry != entry_key
        )

        if can_open:
            if st.button(
                "Open For Review",
                type="primary",
                use_container_width=True,
                key=entry_widget_key("open", entry_key),
            ):
                lock_result = data_manager.start_problem_review(
                    competitor_name,
                    to_write_problem_id(problem_id),
                    judge_name,
                )

                success = bool(lock_result)
                message = ""
                if isinstance(lock_result, dict):
                    success = bool(lock_result.get("success"))
                    message = lock_result.get("message", "")

                if success:
                    st.session_state.active_review_entry = entry_key
                    st.session_state.selected_review_entry = entry_key
                    st.session_state.freeze_table_selection_once = True
                    invalidate_queue_cache()
                    invalidate_problem_payload_cache(entry_key)
                    st.success(message or "Submission locked for your review")
                else:
                    st.error(message or "Unable to open this entry for review")
                st.rerun()

        if locked_by_other:
            st.warning(
                f"This submission is currently under review by {lock_owner}. "
                "You cannot review or decide this entry until it is released or completed."
            )

        if mine_under_review:
            action_col1, action_col2 = st.columns(2)

            with action_col1:
                if st.button(
                    "Approve",
                    type="primary",
                    use_container_width=True,
                    key=entry_widget_key("approve", entry_key),
                ):
                    approved = data_manager.set_judge_approval(
                        competitor_name,
                        to_write_problem_id(problem_id),
                        "approved",
                        judge_id=judge_name,
                        problem_name=(problem_definition or {}).get("title") or problem_data.get("problem_name"),
                    )
                    if approved:
                        if st.session_state.get("active_review_entry") == entry_key:
                            st.session_state.pop("active_review_entry", None)
                        st.session_state.selected_review_entry = entry_key
                        st.session_state.freeze_table_selection_once = True
                        invalidate_queue_cache()
                        invalidate_problem_payload_cache(entry_key)
                        st.success("Submission marked as reviewed and approved")
                    else:
                        st.error("Failed to approve this submission")
                    st.rerun()

            with action_col2:
                if st.button(
                    "Reject",
                    use_container_width=True,
                    key=entry_widget_key("reject", entry_key),
                ):
                    rejected = data_manager.set_judge_approval(
                        competitor_name,
                        to_write_problem_id(problem_id),
                        "rejected",
                        judge_id=judge_name,
                        problem_name=(problem_definition or {}).get("title") or problem_data.get("problem_name"),
                    )
                    if rejected:
                        if st.session_state.get("active_review_entry") == entry_key:
                            st.session_state.pop("active_review_entry", None)
                        st.session_state.selected_review_entry = entry_key
                        st.session_state.freeze_table_selection_once = True
                        invalidate_queue_cache()
                        invalidate_problem_payload_cache(entry_key)
                        st.warning("Submission marked as reviewed and rejected")
                    else:
                        st.error("Failed to reject this submission")
                    st.rerun()

        if current_status == "reviewed":
            if st.session_state.get("active_review_entry") == entry_key:
                st.session_state.pop("active_review_entry", None)
            reviewed_by = (problem_data or {}).get("review_completed_by") or "-"
            reviewed_at = format_timestamp((problem_data or {}).get("review_completed_at") or (problem_data or {}).get("judge_approval_time"))
            st.info(f"Reviewed by {reviewed_by} at {reviewed_at}")

        can_view_code = (
            mine_under_review
            or current_status == "reviewed"
            or (active_review_entry == entry_key and current_status in ["pending_review", "under_review"])
        )
        if can_view_code:
            code = latest_submission.get("code", "No code available")
            st.markdown("**Latest Submitted Code**")
            st.code(code, language="python", line_numbers=True)

            st.markdown("**Test Results**")
            test_results = latest_submission.get("test_results", [])
            if test_results:
                for idx, result in enumerate(test_results, 1):
                    passed = bool(result.get("passed"))
                    status_icon = "PASS" if passed else "FAIL"
                    with st.expander(f"{status_icon} - Test {idx}"):
                        st.write(f"Input: {result.get('input', 'N/A')}")
                        st.write(f"Expected: {result.get('expected', 'N/A')}")
                        st.write(f"Output: {result.get('output', 'N/A')}")
            else:
                st.caption("No test result payload available for this submission.")
        elif can_open:
            st.caption("Open this entry for review to load the submitted code and test details.")

        st.markdown("</div>", unsafe_allow_html=True)


st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
