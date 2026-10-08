"""
PrivacyShield AI - Adaptive Privacy-Utility Optimization for Local LLM-Based Document Processing
Phase 1: Local Document Upload, Text Extraction, Hybrid PII Detection, and Anonymization.

Cybersecurity Dashboard UI with Gradient-Free Palette, Emoji-Free Interface,
and Dedicated Active Processing Animation Experience.
"""

import os
import io
import math
import time
import pandas as pd
import streamlit as st

from modules.document_extractor import extract_text, validate_file_type
from modules.pii_detector import HybridPIIDetector, get_pii_limitations_notice
from modules.anonymizer import PIIAnonymizer
from evaluation import run_full_evaluation


# CLEAN SVG ICONS (NO EMOJIS)
SVG_SHIELD = """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>"""
SVG_FILE = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>"""
SVG_SEARCH = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>"""
SVG_LOCK = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>"""
SVG_CHECK = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#22C55E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>"""
SVG_WARNING = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>"""
SVG_DOWNLOAD = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#F8FAFC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>"""


def format_file_size(size_bytes: int) -> str:
    """Formats byte count into human-readable string (B, KB, MB)."""
    if not size_bytes or size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def mask_sensitive_value(val: str, entity_type: str) -> str:
    """Creates a privacy-preserving preview mask for sensitive detection strings."""
    if not val:
        return ""
    val_str = str(val).strip()
    if len(val_str) <= 3:
        return "*" * len(val_str)
    
    if entity_type == "EMAIL_ADDRESS" and "@" in val_str:
        parts = val_str.split("@", 1)
        uname = parts[0]
        masked_u = uname[0] + "***" + (uname[-1] if len(uname) > 1 else "")
        return f"{masked_u}@{parts[1]}"
    elif entity_type == "PHONE_NUMBER":
        return val_str[:3] + "******" + val_str[-2:] if len(val_str) >= 8 else val_str[0] + "****"
    else:
        return val_str[0] + "***" + val_str[-1]


def set_page_styling():
    """Applies custom CSS styling for a solid-color cybersecurity UI (NO GRADIENTS, NO EMOJIS)."""
    st.markdown(
        """
        <style>
        /* Fonts & Global Styles */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #0B1220;
            color: #F8FAFC;
        }

        /* Main Container Padding & Width */
        .main .block-container {
            padding-top: 1.2rem;
            padding-bottom: 3rem;
            max-width: 1280px;
        }

        /* Custom Solid Cybersecurity Header Banner (NO GRADIENTS) */
        .cyber-header-banner {
            background-color: #111827;
            border: 1px solid #263449;
            border-left: 4px solid #2563EB;
            color: #F8FAFC;
            padding: 1.4rem 1.8rem;
            border-radius: 8px;
            margin-bottom: 1.8rem;
        }
        .header-top-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
        }
        .header-title-box {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .header-icon-box {
            background-color: #172033;
            border: 1px solid #263449;
            padding: 10px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .cyber-header-banner h1 {
            color: #F8FAFC;
            margin: 0;
            font-size: 1.8rem;
            font-weight: 700;
            letter-spacing: -0.3px;
        }
        .cyber-header-banner p {
            color: #94A3B8;
            margin-top: 0.2rem;
            margin-bottom: 0;
            font-size: 0.95rem;
        }
        .security-badge-group {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        .sec-badge {
            background-color: #172033;
            border: 1px solid #263449;
            color: #94A3B8;
            font-size: 0.78rem;
            font-weight: 600;
            padding: 0.3rem 0.75rem;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .sec-badge.active {
            border-color: #22C55E;
            color: #22C55E;
            background-color: #064E3B;
        }
        .dot-green {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background-color: #22C55E;
        }

        /* Dedicated Animated Processing Overlay Card */
        .processing-card-container {
            background-color: #111827;
            border: 1px solid #2563EB;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.8rem;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        }
        .processing-title-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
        }
        .processing-title-text {
            font-size: 0.92rem;
            font-weight: 700;
            color: #38BDF8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Cyber Data Scanner Bar */
        .cyber-scan-track {
            width: 100%;
            height: 6px;
            background-color: #172033;
            border-radius: 4px;
            overflow: hidden;
            position: relative;
            margin-bottom: 1.2rem;
        }
        .cyber-scan-bar {
            height: 100%;
            width: 35%;
            background-color: #2563EB;
            position: absolute;
            animation: cyber-scan-move 1.8s infinite ease-in-out;
            border-radius: 4px;
        }
        @keyframes cyber-scan-move {
            0% { left: -35%; }
            50% { left: 100%; }
            100% { left: -35%; }
        }

        /* Processing Nodes List */
        .processing-nodes-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
            gap: 10px;
        }
        .proc-node {
            background-color: #172033;
            border: 1px solid #263449;
            border-radius: 6px;
            padding: 0.75rem;
            font-size: 0.82rem;
            font-weight: 600;
            color: #64748B;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
        }
        .proc-node.active {
            border-color: #38BDF8;
            color: #F8FAFC;
            background-color: #1E293B;
        }
        .proc-node.completed {
            border-color: #22C55E;
            color: #22C55E;
            background-color: #064E3B;
        }
        .node-indicator {
            width: 16px; height: 16px;
            border-radius: 50%;
            border: 2px solid #64748B;
            display: flex; align-items: center; justify-content: center;
            font-size: 0.65rem; font-weight: 700;
        }
        .proc-node.active .node-indicator { border-color: #38BDF8; color: #38BDF8; }
        .proc-node.completed .node-indicator { border-color: #22C55E; background-color: #22C55E; color: #0B1220; }

        /* Section Cards & Surfaces */
        .content-card-solid {
            background-color: #111827;
            border: 1px solid #263449;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }

        /* Monospaced Code Text Container */
        .text-box-container {
            background-color: #090E17;
            border: 1px solid #263449;
            border-radius: 6px;
            padding: 1.2rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.88rem;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
            max-height: 480px;
            overflow-y: auto;
            color: #F8FAFC;
        }

        /* Metric Highlights */
        div[data-testid="stMetricValue"] {
            font-size: 1.6rem !important;
            font-weight: 700 !important;
            color: #38BDF8 !important;
        }

        /* Limitations Box */
        .limitation-box-solid {
            background-color: #172033;
            border: 1px solid #F59E0B;
            border-left: 4px solid #F59E0B;
            padding: 1rem 1.2rem;
            border-radius: 6px;
            color: #CBD5E1;
            font-size: 0.88rem;
            line-height: 1.5;
            margin-top: 1.2rem;
        }
        .limitation-box-solid b {
            color: #F59E0B;
        }

        /* Output Banner */
        .success-banner-solid {
            background-color: #064E3B;
            border: 1px solid #22C55E;
            border-left: 5px solid #22C55E;
            padding: 1.2rem 1.5rem;
            border-radius: 6px;
            margin-bottom: 1.5rem;
            color: #F8FAFC;
        }
        .success-banner-solid h3 {
            margin: 0 0 0.3rem 0;
            color: #22C55E;
            font-size: 1.15rem;
            font-weight: 700;
        }
        .success-banner-solid p {
            margin: 0;
            color: #A7F3D0;
            font-size: 0.92rem;
        }

        /* Sidebar Styling */
        .sidebar-brand-box {
            display: flex;
            align-items: center;
            gap: 10px;
            padding-bottom: 1rem;
            border-bottom: 1px solid #263449;
            margin-bottom: 1rem;
        }
        .sidebar-brand-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #F8FAFC;
            letter-spacing: -0.3px;
        }
        .sidebar-brand-sub {
            font-size: 0.72rem;
            color: #38BDF8;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .status-card-sidebar {
            background-color: #172033;
            border: 1px solid #263449;
            border-radius: 6px;
            padding: 0.8rem;
            margin-bottom: 1.2rem;
            font-size: 0.82rem;
        }
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
            color: #94A3B8;
        }
        .status-item:last-child { margin-bottom: 0; }

        /* Custom Table Styling */
        .dataframe {
            font-size: 0.88rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


@st.cache_resource
def load_pii_detector():
    """Cached initialization of Hybrid PII Detector."""
    return HybridPIIDetector()


def render_header():
    """Renders the top cybersecurity header banner with clean SVG icon (NO EMOJIS, NO GRADIENTS)."""
    st.markdown(
        f"""
        <div class="cyber-header-banner">
            <div class="header-top-row">
                <div class="header-title-box">
                    <div class="header-icon-box">{SVG_SHIELD}</div>
                    <div>
                        <h1>PrivacyShield AI</h1>
                        <p>Privacy-focused document processing with hybrid PII detection and anonymization.</p>
                    </div>
                </div>
                <div class="security-badge-group">
                    <span class="sec-badge active"><span class="dot-green"></span> Engine Ready</span>
                    <span class="sec-badge">Local Memory Execution</span>
                    <span class="sec-badge">Presidio + Regex</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_processing_animation(active_step: int, status_msg: str):
    """
    Renders the dedicated animated processing experience ONLY while active.
    
    Args:
        active_step (int): Current active stage (1 to 5).
        status_msg (str): Message describing the current execution phase.
    """
    stages = [
        (1, "Uploading Document"),
        (2, "Extracting Text"),
        (3, "Detecting PII"),
        (4, "Anonymizing Content"),
        (5, "Processing Complete"),
    ]

    nodes_html = ""
    for num, label in stages:
        if num < active_step:
            node_cls = "completed"
            ind_content = "✓"
        elif num == active_step:
            node_cls = "active"
            ind_content = str(num)
        else:
            node_cls = ""
            ind_content = str(num)

        nodes_html += f"""
        <div class="proc-node {node_cls}">
            <div class="node-indicator">{ind_content}</div>
            <span>{label}</span>
        </div>
        """

    st.markdown(
        f"""
        <div class="processing-card-container">
            <div class="processing-title-bar">
                <span class="processing-title-text">PROCESSING SECURITY PIPELINE</span>
                <span style="color: #94A3B8; font-size: 0.82rem;">{status_msg}</span>
            </div>
            <div class="cyber-scan-track">
                <div class="cyber-scan-bar"></div>
            </div>
            <div class="processing-nodes-grid">
                {nodes_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def init_session_state():
    """Initializes session state variables cleanly."""
    defaults = {
        "extracted_text": None,
        "filename": None,
        "file_bytes": None,
        "file_size": None,
        "extraction_error": None,
        "detection_results": None,
        "detection_error": None,
        "anonymized_text": None,
        "anonymization_metadata": None,
        "anonymization_error": None,
        "eval_results": None,
        "mask_pii_table": True,
        "is_processing_active": False,
        "processing_step": 1,
        "processing_msg": "Initializing..."
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def reset_downstream_state():
    """Resets detection and anonymization states."""
    st.session_state.detection_results = None
    st.session_state.detection_error = None
    st.session_state.anonymized_text = None
    st.session_state.anonymization_metadata = None
    st.session_state.anonymization_error = None


def reset_all_state():
    """Fully resets all session state variables."""
    st.session_state.extracted_text = None
    st.session_state.filename = None
    st.session_state.file_bytes = None
    st.session_state.file_size = None
    st.session_state.extraction_error = None
    st.session_state.is_processing_active = False
    st.session_state.processing_step = 1
    reset_downstream_state()


def run_full_pipeline(file_bytes: bytes, filename: str, detector: HybridPIIDetector, anonymizer: PIIAnonymizer, score_threshold: float, selected_entities: list, strategy_code: str):
    """
    Executes the full processing sequence while driving the active processing animation.
    """
    st.session_state.is_processing_active = True
    
    # Stage 1: Uploading
    st.session_state.processing_step = 1
    st.session_state.processing_msg = "Uploading document into secure memory..."
    
    # Stage 2: Extracting Text
    st.session_state.processing_step = 2
    st.session_state.processing_msg = "Extracting raw text content..."
    try:
        extracted = extract_text(file_bytes, filename)
        st.session_state.extracted_text = extracted
        st.session_state.filename = filename
        st.session_state.file_bytes = file_bytes
        st.session_state.file_size = len(file_bytes)
        st.session_state.extraction_error = None
    except Exception as e:
        st.session_state.extraction_error = str(e)
        st.session_state.is_processing_active = False
        return

    # Stage 3: Detecting PII
    st.session_state.processing_step = 3
    st.session_state.processing_msg = "Scanning document for PII entities using Presidio and regex..."
    try:
        results = detector.analyze_text(
            text=extracted,
            score_threshold=score_threshold,
            entities=selected_entities
        )
        st.session_state.detection_results = results
        st.session_state.detection_error = None
    except Exception as e:
        st.session_state.detection_error = str(e)
        st.session_state.is_processing_active = False
        return

    # Stage 4: Anonymizing
    st.session_state.processing_step = 4
    st.session_state.processing_msg = "Applying selected anonymization transformation..."
    try:
        anon_text, meta = anonymizer.anonymize(
            text=extracted,
            detection_results=results,
            strategy=strategy_code
        )
        st.session_state.anonymized_text = anon_text
        st.session_state.anonymization_metadata = meta
        st.session_state.anonymization_error = None
    except Exception as e:
        st.session_state.anonymization_error = str(e)
        st.session_state.is_processing_active = False
        return

    # Stage 5: Complete
    st.session_state.processing_step = 5
    st.session_state.processing_msg = "Processing completed successfully."
    st.session_state.is_processing_active = False


def main():
    st.set_page_config(
        page_title="PrivacyShield AI - Hybrid PII Anonymizer",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    set_page_styling()
    init_session_state()

    detector = load_pii_detector()
    anonymizer = PIIAnonymizer()

    # SIDEBAR NAVIGATION & CONFIGURATION (NO EMOJIS)
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand-box">
                <div>{SVG_SHIELD}</div>
                <div>
                    <div class="sidebar-brand-title">PrivacyShield AI</div>
                    <div class="sidebar-brand-sub">Privacy Processing Engine</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="status-card-sidebar">
                <div class="status-item"><span class="dot-green"></span> System: Operational</div>
                <div class="status-item">Local Memory Execution</div>
                <div class="status-item">Zero Cloud Retention</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.subheader("Detection Settings")
        selected_entities = st.multiselect(
            "Target Entity Categories",
            options=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION"],
            default=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION"],
            help="Select PII entity categories to scan."
        )

        score_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.10,
            max_value=1.00,
            value=0.40,
            step=0.05,
            help="Minimum confidence threshold for classifying PII."
        )

        st.markdown("---")
        st.subheader("Anonymization Strategy")
        strategy_option = st.radio(
            "Replacement Mode",
            options=["Type-Based Replacement", "Redaction"],
            index=0,
            help=(
                "Type-Based: Replaces PII with indexed labels like [PERSON_1], [EMAIL_1].\n"
                "Redaction: Replaces all PII with [REDACTED]."
            )
        )
        strategy_code = "type_based" if strategy_option == "Type-Based Replacement" else "redact"

        st.markdown("---")
        st.subheader("Quick Actions")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("Load Sample", use_container_width=True, help="Load sample_pii.txt"):
                sample_path = os.path.join("sample_documents", "sample_pii.txt")
                if os.path.exists(sample_path):
                    try:
                        with open(sample_path, "rb") as f:
                            s_bytes = f.read()
                        reset_all_state()
                        run_full_pipeline(s_bytes, "sample_pii.txt", detector, anonymizer, score_threshold, selected_entities, strategy_code)
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Failed to load sample: {ex}")
                else:
                    st.error("Sample file sample_documents/sample_pii.txt not found.")
        with col_s2:
            if st.button("Clear All", use_container_width=True, help="Reset session state"):
                reset_all_state()
                st.rerun()

    # RENDER MAIN HEADER (NO EMOJIS, NO GRADIENTS, NO PERMANENT STEPPER)
    render_header()

    # RENDER ANIMATED PROCESSING OVERLAY ONLY WHILE ACTIVE
    if st.session_state.is_processing_active:
        render_processing_animation(st.session_state.processing_step, st.session_state.processing_msg)

    # MAIN WORKFLOW TABS
    tab1, tab2, tab3, tab4 = st.tabs([
        "Document Upload & Extraction",
        "Hybrid PII Detection",
        "Anonymization & Protected Output",
        "Evaluation & Benchmarks"
    ])

    # ==========================================
    # TAB 1: DOCUMENT UPLOAD & EXTRACTION
    # ==========================================
    with tab1:
        st.markdown("### Document Upload & Extraction")
        st.write("Upload a `.txt`, `.pdf`, or `.docx` file to process locally.")

        uploaded_file = st.file_uploader(
            "Upload Document",
            type=["txt", "pdf", "docx"],
            help="Supported formats: PDF, DOCX, TXT. Max size: 10MB.",
            label_visibility="collapsed"
        )

        if uploaded_file is not None:
            filename = uploaded_file.name
            file_bytes = uploaded_file.getvalue()

            # Check if file changed
            if st.session_state.filename != filename or st.session_state.file_bytes != file_bytes:
                reset_all_state()
                with st.spinner("Processing document security pipeline..."):
                    run_full_pipeline(file_bytes, filename, detector, anonymizer, score_threshold, selected_entities, strategy_code)
                st.rerun()

        if st.session_state.extraction_error:
            st.error(f"Document Extraction Error: {st.session_state.extraction_error}")

        if st.session_state.extracted_text:
            st.success(f"Successfully extracted text from `{st.session_state.filename}`")

            # File Info Metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("File Name", st.session_state.filename)
            m2.metric("Format", validate_file_type(st.session_state.filename).upper())
            m3.metric("File Size", format_file_size(st.session_state.file_size or 0))
            m4.metric("Word Count", f"{len(st.session_state.extracted_text.split()):,}")

            st.markdown("#### Extracted Text Preview")
            st.markdown(
                f'<div class="text-box-container">{st.session_state.extracted_text}</div>',
                unsafe_allow_html=True
            )

            col_btn1, _ = st.columns([1, 4])
            with col_btn1:
                if st.button("Remove File", use_container_width=True):
                    reset_all_state()
                    st.rerun()
        elif not st.session_state.file_bytes:
            st.info("Drag and drop a document above or click **'Load Sample'** in the sidebar to process.")

    # ==========================================
    # TAB 2: HYBRID PII DETECTION
    # ==========================================
    with tab2:
        st.markdown("### Hybrid PII Detection Engine")
        st.write("Scans extracted document text using Microsoft Presidio and custom regex recognizers.")

        if not st.session_state.extracted_text:
            st.warning("Please upload a document in Module 1 first.")
        else:
            col_run1, _ = st.columns([2, 3])
            with col_run1:
                run_detection_btn = st.button("Run PII Detection", type="primary", use_container_width=True)

            if run_detection_btn:
                try:
                    with st.spinner("Scanning document for PII entities..."):
                        results = detector.analyze_text(
                            text=st.session_state.extracted_text,
                            score_threshold=score_threshold,
                            entities=selected_entities
                        )
                        st.session_state.detection_results = results
                        st.session_state.detection_error = None
                        # Update anonymization text if detection changes
                        anon_text, meta = anonymizer.anonymize(
                            text=st.session_state.extracted_text,
                            detection_results=results,
                            strategy=strategy_code
                        )
                        st.session_state.anonymized_text = anon_text
                        st.session_state.anonymization_metadata = meta
                        st.rerun()
                except Exception as e:
                    st.session_state.detection_error = str(e)
                    st.session_state.detection_results = None

            if st.session_state.detection_error:
                st.error(f"PII Detection Error: {st.session_state.detection_error}")

            if st.session_state.detection_results is not None:
                results = st.session_state.detection_results

                # Metrics Summary
                d1, d2, d3, d4 = st.columns(4)
                d1.metric("Total PII Detected", len(results))
                unique_types = len(set(r.entity_type for r in results)) if results else 0
                d2.metric("Unique Entity Types", unique_types)
                high_conf = len([r for r in results if r.score >= 0.8]) if results else 0
                d3.metric("High Confidence (≥0.80)", high_conf)
                d4.metric("Detection Engine", "Presidio + Regex")

                st.markdown("---")

                # Table Header & Privacy Mask Toggle
                col_tbl_h, col_mask = st.columns([3, 1])
                with col_tbl_h:
                    st.markdown("#### Detected Entities Summary")
                with col_mask:
                    mask_toggle = st.checkbox(
                        "Privacy Preview Mask",
                        value=st.session_state.mask_pii_table,
                        help="Mask sensitive values in table for safe demonstration."
                    )
                    st.session_state.mask_pii_table = mask_toggle

                if results:
                    df_rows = []
                    for r in results:
                        display_val = mask_sensitive_value(r.text, r.entity_type) if mask_toggle else r.text
                        df_rows.append({
                            "Entity Category": r.entity_type,
                            "Detected Value": display_val,
                            "Position Span": f"{r.start} - {r.end}",
                            "Confidence Score": f"{r.score:.2f}",
                            "Status": "Detected"
                        })
                    
                    df = pd.DataFrame(df_rows)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No PII entities detected based on current filter and confidence threshold settings.")

                # Limitations Notice
                st.markdown(
                    f"""
                    <div class="limitation-box-solid">
                        <b>Automated PII Detection Notice:</b><br/>
                        {get_pii_limitations_notice()}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # ==========================================
    # TAB 3: ANONYMIZATION & PROTECTED OUTPUT
    # ==========================================
    with tab3:
        st.markdown("### PII Anonymization & Protected Output")
        st.write("Applies selected anonymization strategy to produce a privacy-protected document output.")

        if not st.session_state.extracted_text:
            st.warning("Please upload a document in Module 1 first.")
        elif st.session_state.detection_results is None:
            st.warning("Please run PII Detection in Module 2 before anonymization.")
        else:
            results = st.session_state.detection_results

            col_anon_btn, _ = st.columns([2, 3])
            with col_anon_btn:
                generate_anon_btn = st.button("Generate Protected Text", type="primary", use_container_width=True)

            if generate_anon_btn or st.session_state.anonymized_text is not None:
                if generate_anon_btn:
                    try:
                        with st.spinner("Applying anonymization transformation..."):
                            anon_text, meta = anonymizer.anonymize(
                                text=st.session_state.extracted_text,
                                detection_results=results,
                                strategy=strategy_code
                            )
                            st.session_state.anonymized_text = anon_text
                            st.session_state.anonymization_metadata = meta
                            st.session_state.anonymization_error = None
                            st.rerun()
                    except Exception as e:
                        st.session_state.anonymization_error = str(e)
                        st.session_state.anonymized_text = None

                if st.session_state.anonymization_error:
                    st.error(f"Anonymization Error: {st.session_state.anonymization_error}")

                if st.session_state.anonymized_text is not None:
                    anon_text = st.session_state.anonymized_text
                    meta = st.session_state.anonymization_metadata or {}

                    # SUCCESS BANNER (NO GRADIENT, SOLID GREEN)
                    st.markdown(
                        f"""
                        <div class="success-banner-solid">
                            <h3>Protected Document Output Ready</h3>
                            <p>Anonymized <b>{meta.get('total_anonymized', 0)}</b> PII entities using <b>{strategy_option}</b>.</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # SIDE-BY-SIDE COMPARISON PANELS
                    col_orig, col_anon = st.columns(2)

                    with col_orig:
                        st.markdown("#### Original Text")
                        st.markdown(
                            f'<div class="text-box-container">{st.session_state.extracted_text}</div>',
                            unsafe_allow_html=True
                        )

                    with col_anon:
                        st.markdown("#### Protected Text")
                        st.markdown(
                            f'<div class="text-box-container">{anon_text}</div>',
                            unsafe_allow_html=True
                        )

                    st.markdown("---")

                    # REPLACEMENT MAPPING TABLE
                    rep_map = meta.get("replacement_map", {})
                    if rep_map:
                        with st.expander("View Entity Replacement Mapping Table", expanded=False):
                            rep_rows = [
                                {
                                    "Original Snippet": mask_sensitive_value(k, "TEXT") if st.session_state.mask_pii_table else k,
                                    "Anonymized Replacement": v
                                }
                                for k, v in rep_map.items()
                            ]
                            st.dataframe(pd.DataFrame(rep_rows), use_container_width=True, hide_index=True)

                    # DOWNLOAD & ACTION SECTION
                    st.markdown("#### Protected Output Actions")
                    out_filename = f"protected_{st.session_state.filename or 'document.txt'}"
                    if not out_filename.endswith(".txt"):
                        out_filename = os.path.splitext(out_filename)[0] + ".txt"

                    d_col1, d_col2 = st.columns([2, 3])
                    with d_col1:
                        st.download_button(
                            label="Download Protected Document (.txt)",
                            data=anon_text,
                            file_name=out_filename,
                            mime="text/plain",
                            type="primary",
                            use_container_width=True
                        )
                    with d_col2:
                        st.info(f"Protected output file ready: `{out_filename}`")

    # ==========================================
    # TAB 4: EVALUATION & BENCHMARKS
    # ==========================================
    with tab4:
        st.markdown("### System Evaluation & Performance Benchmarks")
        st.write(
            "Executes automated benchmark evaluation for Text Extraction, Hybrid PII Detection, "
            "Anonymization Strategies, Residual PII Rate, and Context Preservation."
        )

        col_eval_btn, _ = st.columns([2, 3])
        with col_eval_btn:
            run_eval_btn = st.button("Run Full Evaluation Suite", type="primary", use_container_width=True)

        if run_eval_btn:
            with st.spinner("Running evaluation benchmark suite across all system modules..."):
                st.session_state.eval_results = run_full_evaluation()
            st.rerun()

        if st.session_state.eval_results is not None:
            eval_res = st.session_state.eval_results
            ext_r = eval_res["extraction"]
            det_r = eval_res["detection"]
            anon_r = eval_res["anonymization"]
            res_r = eval_res["residual_pii"]
            ctx_r = eval_res["context_preservation"]

            # TOP LEVEL METRICS SUMMARY
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Extraction Success Rate", f"{ext_r['success_rate_pct']}%")
            k2.metric("PII Detection F1-Score", f"{det_r['f1_score']:.4f}")
            k3.metric("Anonymization Success Rate", f"{anon_r['success_rate_pct']}%")
            k4.metric("Residual PII Rate", f"{res_r['residual_pii_rate_pct']}%")

            st.markdown("---")

            # 1. TEXT EXTRACTION PERFORMANCE
            st.markdown("#### 1. Text Extraction Success Rate")
            st.markdown(
                f"**Success Rate:** `{ext_r['success_rate_pct']}%` | "
                f"**Valid Documents Passed:** `{ext_r['valid_formats_passed']}` | "
                f"**Total Scenarios Tested:** `{ext_r['total_tested']}`"
            )
            df_ext = pd.DataFrame([
                {
                    "File Format": r["format"],
                    "Test Scenario": r["test_type"],
                    "Status": "Passed" if r["success"] else "Failed",
                    "Details / Error": r["error"] or "Extracted cleanly"
                }
                for r in ext_r["detailed_results"]
            ])
            st.dataframe(df_ext, use_container_width=True, hide_index=True)

            st.markdown("---")

            # 2. HYBRID PII DETECTION METRICS
            st.markdown("#### 2. Hybrid PII Detection Metrics (Ground-Truth Evaluated)")
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("True Positives (TP)", det_r["true_positives"])
            m_col2.metric("Precision", f"{det_r['precision']:.4f}")
            m_col3.metric("Recall", f"{det_r['recall']:.4f}")
            m_col4.metric("F1-Score", f"{det_r['f1_score']:.4f}")

            st.markdown("##### Per-Category Performance Breakdown")
            cat_rows = []
            for cat, c_m in det_r["category_metrics"].items():
                cat_rows.append({
                    "Entity Category": cat,
                    "TP": c_m["tp"],
                    "FP": c_m["fp"],
                    "FN": c_m["fn"],
                    "Precision": f"{c_m['precision']:.4f}",
                    "Recall": f"{c_m['recall']:.4f}",
                    "F1-Score": f"{c_m['f1']:.4f}"
                })
            st.dataframe(pd.DataFrame(cat_rows), use_container_width=True, hide_index=True)

            st.markdown("---")

            # 3. ANONYMIZATION PERFORMANCE
            st.markdown("#### 3. Anonymization Strategy Verification")
            st.markdown(
                f"**Success Rate:** `{anon_r['success_rate_pct']}%` | "
                f"**Verification Checks Passed:** `{anon_r['passed_checks']}/{anon_r['total_checks']}`"
            )
            df_anon = pd.DataFrame([
                {
                    "Verification Criterion": c["criterion"],
                    "Status": "Passed" if c["passed"] else "Failed",
                    "Details": c["details"]
                }
                for c in anon_r["checks"]
            ])
            st.dataframe(df_anon, use_container_width=True, hide_index=True)

            st.markdown("---")

            # 4. RESIDUAL PII RATE
            st.markdown("#### 4. Residual PII Rate Evaluation")
            res_c1, res_c2, res_c3 = st.columns(3)
            res_c1.metric("Original PII Detected", res_r["original_pii_detected"])
            res_c2.metric("Residual PII Detected", res_r["residual_pii_detected"])
            res_c3.metric("Residual PII Rate", f"{res_r['residual_pii_rate_pct']}%")

            st.markdown(
                f"""
                <div class="limitation-box-solid">
                    <b>Residual PII Indicator Notice:</b><br/>
                    {res_r['disclaimer']}
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("---")

            # 5. CONTEXT PRESERVATION
            st.markdown("#### 5. Context Preservation Analysis")
            st.markdown(
                f"**Non-PII Word Retention Rate:** `{ctx_r['non_pii_word_retention_rate_pct']}%` "
                f"({ctx_r['retained_words_count']}/{ctx_r['total_non_pii_words_count']} non-sensitive tokens retained)"
            )
            q_eval = ctx_r["qualitative_evaluation"]
            st.markdown(
                f"""
                <div class="success-banner-solid">
                    <b>Qualitative Syntactic Structure Benchmark:</b><br/>
                    Original: <code>"{q_eval['sample_original']}"</code><br/>
                    Anonymized: <code>"{q_eval['sample_anonymized']}"</code><br/><br/>
                    <b>Observation:</b> {q_eval['observation']}
                </div>
                """,
                unsafe_allow_html=True
            )


if __name__ == "__main__":
    main()
