import streamlit as st
import uuid
import re
import textwrap
from pathlib import Path
from datetime import datetime
import cv2
import numpy as np
from PIL import Image
import io

from sheets_helper import (
    get_worksheet,
    initialize_sheet,
    add_ticket,
    get_pending_tickets,
    get_all_tickets,
    update_ticket_status,
    find_ticket_by_uuid,
)
from qr_helper import generate_qr_code, generate_branded_ticket_image
from delivery_helper import send_ticket_email, send_ticket_whatsapp

def render_html(markup: str):
    """Render HTML without Markdown treating indentation as a code block."""
    st.markdown(textwrap.dedent(markup).strip(), unsafe_allow_html=True)

# Page config - MUST be first
st.set_page_config(
    page_title="The Notebook Concert - Ticketing System",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="collapsed",
)

try:
    from pyzbar.pyzbar import decode
    PYZBAR_AVAILABLE = True
except Exception:
    PYZBAR_AVAILABLE = False

# Custom CSS for styling
st.markdown("""
    <style>
    :root {
        --brand: #c026d3; /* magenta */
        --brand-dark: #a21caf; /* deep magenta */
        --accent: #a855f7; /* purple */
        --ink: #ffffff;
        --muted: rgba(255, 255, 255, 0.87);
        --line: rgba(255, 255, 255, 0.25);
        --panel: rgba(255, 255, 255, 0.12);
        --soft: rgba(255, 255, 255, 0.10);
        --blue-soft: rgba(56, 189, 248, 0.15);
        --green-soft: rgba(34, 197, 94, 0.15);
        --shadow: 0 18px 50px rgba(0, 0, 0, 0.45);
    }
    .stApp {
        background:
          radial-gradient(900px 420px at 14% 10%, rgba(168, 85, 247, 0.28), transparent 60%),
          radial-gradient(820px 420px at 86% 6%, rgba(192, 38, 211, 0.22), transparent 60%),
          linear-gradient(180deg, #070810 0%, #0b0c16 55%, #0a0b12 100%);
    }
    [data-testid="stHeader"] {
        background: transparent;
    }
    section[data-testid="stSidebar"] {
        display: none;
    }
    .block-container {
        max-width: 1180px;
        padding-top: 3rem;
        padding-bottom: 2rem;
    }
    .main {
        padding: 1.5rem;
    }
    .header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeeba;
    }
    .booking-hero {
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .booking-eyebrow {
        color: rgba(255, 255, 255, 0.95);
        font-size: 0.88rem;
        font-weight: 900;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }
    .booking-title {
        color: var(--ink);
        font-size: clamp(2rem, 4vw, 3.1rem);
        font-weight: 800;
        line-height: 1.05;
        margin: 0;
    }
    .booking-copy {
        color: var(--muted);
        font-size: 1rem;
        max-width: 680px;
        margin-top: 0.8rem;
        margin-left: auto;
        margin-right: auto;
    }
    .booking-steps {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 1.4rem 0 1.6rem;
    }
    .step-pill {
        align-items: center;
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        color: var(--muted);
        display: flex;
        gap: 0.65rem;
        min-height: 58px;
        padding: 0.75rem 0.9rem;
    }
    .step-pill:not(.active) {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.22);
        color: rgba(255, 255, 255, 0.92);
    }
    .step-pill.active {
        border-color: rgba(168, 85, 247, 0.40);
        box-shadow: 0 10px 26px rgba(168, 85, 247, 0.16);
        color: var(--ink);
    }
    .step-index {
        align-items: center;
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.22);
        border-radius: 999px;
        display: inline-flex;
        flex: 0 0 30px;
        font-size: 0.85rem;
        font-weight: 800;
        height: 30px;
        justify-content: center;
        color: rgba(255, 255, 255, 0.95);
    }
    .step-pill.active .step-index {
        background: var(--brand);
        color: #ffffff;
        border-color: rgba(255, 255, 255, 0.18);
    }
    .step-text {
        font-size: 0.92rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .booking-layout {
        margin-top: 0.25rem;
    }
    .booking-layout [data-testid="column"] > div {
        height: 100%;
    }
    .booking-layout div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: var(--shadow);
        height: 100%;
    }
    .booking-panel {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: var(--shadow);
        min-height: 100%;
        padding: 1.35rem;
    }
    .panel-title {
        color: var(--ink);
        font-size: 1.35rem;
        font-weight: 800;
        margin: 0;
    }
    .panel-copy {
        color: var(--muted);
        font-size: 0.92rem;
        margin: 0.35rem 0 1.1rem;
    }
    .amount-row {
        align-items: center;
        background: var(--soft);
        border: 1px solid var(--line);
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        margin-bottom: 1rem;
        padding: 0.85rem 1rem;
    }
    .amount-label {
        color: var(--muted);
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .amount-value {
        color: var(--ink);
        font-size: 1.45rem;
        font-weight: 850;
    }
    .quantity-control {
        background: var(--soft);
        border: 1px solid var(--line);
        border-radius: 8px;
        margin: 0.4rem 0 1rem;
        padding: 0.8rem 0.9rem 0.4rem;
    }
    .quantity-title {
        color: var(--ink);
        font-size: 0.94rem;
        font-weight: 800;
        margin-bottom: 0.15rem;
    }
    .quantity-caption {
        color: var(--muted);
        font-size: 0.82rem;
        margin-bottom: 0.45rem;
    }
    .quantity-value {
        align-items: center;
        background: rgba(0, 0, 0, 0.18);
        border: 1px solid var(--line);
        border-radius: 8px;
        color: var(--ink);
        display: flex;
        font-size: 1.35rem;
        font-weight: 850;
        justify-content: center;
        min-height: 46px;
    }
    .delivery-note {
        background: rgba(56, 189, 248, 0.15);
        border: 1px solid rgba(56, 189, 248, 0.4);
        border-radius: 8px;
        color: #60d5ff;
        font-size: 0.9rem;
        line-height: 1.45;
        margin-top: 0.75rem;
        padding: 0.85rem 0.9rem;
    }
    .confirmation-shell {
        margin: 1.5rem auto 0;
        max-width: 760px;
    }
    .confirmation-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        box-shadow: 0 18px 42px rgba(31, 41, 55, 0.08);
        padding: 1.5rem;
    }
    .confirmation-icon {
        align-items: center;
        background: #dcfce7;
        border-radius: 999px;
        color: #166534;
        display: flex;
        font-size: 1.35rem;
        font-weight: 900;
        height: 46px;
        justify-content: center;
        margin-bottom: 1rem;
        width: 46px;
    }
    .confirmation-title {
        color: #1f2937;
        font-size: clamp(1.7rem, 4vw, 2.35rem);
        font-weight: 850;
        line-height: 1.1;
        margin: 0 0 0.45rem;
    }
    .confirmation-copy {
        color: #4b5563;
        font-size: 1rem;
        line-height: 1.55;
        margin: 0 0 1.2rem;
    }
    .summary-grid {
        display: grid;
        gap: 0.75rem;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        margin: 1.1rem 0;
    }
    .summary-item.wide {
        grid-column: 1 / -1;
    }
    .summary-item {
        background: #f3f4f6;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.85rem;
    }
    .summary-label {
        color: #6b7280;
        font-size: 0.76rem;
        font-weight: 800;
        text-transform: uppercase;
    }
    .summary-value {
        color: #1f2937;
        font-size: 1rem;
        font-weight: 850;
        margin-top: 0.25rem;
        overflow-wrap: anywhere;
    }
    .delivery-list {
        display: grid;
        gap: 0.7rem;
        margin-top: 1rem;
    }
    .delivery-row {
        align-items: flex-start;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        display: flex;
        gap: 0.75rem;
        padding: 0.85rem;
        background: #f9fafb;
    }
    .delivery-row.success {
        background: #ecfdf5;
        border-color: #86efac;
    }
    .delivery-row.warning {
        background: #fef3c7;
        border-color: #fde047;
    }
    .delivery-status-icon {
        align-items: center;
        border-radius: 999px;
        display: flex;
        flex: 0 0 28px;
        font-size: 0.92rem;
        font-weight: 900;
        height: 28px;
        justify-content: center;
        width: 28px;
    }
    .delivery-row.success .delivery-status-icon {
        background: #16a34a;
        color: #ffffff;
    }
    .delivery-row.warning .delivery-status-icon {
        background: #d97706;
        color: #ffffff;
    }
    .delivery-title {
        color: #1f2937;
        font-weight: 850;
        margin-bottom: 0.15rem;
    }
    .delivery-copy {
        color: #4b5563;
        font-size: 0.92rem;
        line-height: 1.45;
    }
    .booking-id-full {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.92rem;
        line-height: 1.45;
    }
    .payment-card {
        text-align: center;
    }
    .booking-layout [data-testid="stImage"] {
        background: rgba(0, 0, 0, 0.18);
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: var(--shadow);
        margin: 0 auto;
        max-width: 300px;
        padding: 0.75rem;
    }
    .payment-placeholder {
        align-items: center;
        background: var(--blue-soft);
        border: 1px dashed #b6d9ff;
        border-radius: 8px;
        color: #1f5f99;
        display: flex;
        min-height: 280px;
        justify-content: center;
        padding: 1.5rem;
        text-align: center;
    }
    .payment-done {
        background: var(--green-soft);
        border: 1px solid rgba(34, 197, 94, 0.45);
        border-radius: 8px;
        color: rgba(220, 252, 231, 0.96);
        font-weight: 800;
        margin: 0.9rem 0 0.2rem;
        padding: 0.8rem 0.9rem;
        text-align: center;
    }
    /* Header styling */
    .header-contact {
        background: linear-gradient(90deg, rgba(168, 85, 247, 0.15), rgba(192, 38, 211, 0.15));
        border: 1px solid rgba(192, 38, 211, 0.4);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 24px rgba(168, 85, 247, 0.1);
    }
    .header-contact-title {
        color: rgba(255, 255, 255, 0.95);
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: 0.8rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .header-contact-phones {
        display: flex;
        justify-content: center;
        gap: 2rem;
        flex-wrap: wrap;
    }
    .header-contact-phone {
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .header-contact-phone a {
        color: #a855f7;
        font-size: 1.1rem;
        font-weight: 700;
        text-decoration: none;
        transition: all 0.3s ease;
    }
    .header-contact-phone a:hover {
        color: #c026d3;
        filter: brightness(1.15);
    }
    .header-contact-icon {
        font-size: 1.3rem;
    }
    @media (max-width: 768px) {
        .header-contact {
            padding: 1rem 1.2rem;
            margin-bottom: 1.5rem;
        }
        .header-contact-title {
            font-size: 0.9rem;
            margin-bottom: 0.6rem;
        }
        .header-contact-phones {
            gap: 1.2rem;
        }
        .header-contact-phone a {
            font-size: 1rem;
        }
        .header-contact-icon {
            font-size: 1.1rem;
        }
    }
    @media (max-width: 480px) {
        .header-contact {
            padding: 0.9rem 1rem;
            margin-bottom: 1.2rem;
            border-radius: 8px;
        }
        .header-contact-title {
            font-size: 0.8rem;
            margin-bottom: 0.5rem;
        }
        .header-contact-phones {
            flex-direction: column;
            gap: 0.8rem;
        }
        .header-contact-phone a {
            font-size: 0.95rem;
        }
    }
    /* Full-screen blurred overlay for spinner */
    div[data-testid="stSpinner"] {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        z-index: 9999 !important;
        background: rgba(0, 0, 0, 0.65) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
    }
    /* Spinner container - make it bigger with text */
    div[data-testid="stSpinner"] > div {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 3rem !important;
        width: auto !important;
        height: auto !important;
    }
    /* Spinner icon styling */
    div[data-testid="stSpinner"] svg,
    div[data-testid="stSpinner"] > div > svg {
        width: 200px !important;
        height: 200px !important;
        min-width: 200px !important;
        min-height: 200px !important;
        stroke-width: 2px !important;
        filter: drop-shadow(0 0 30px rgba(192, 38, 211, 0.8)) !important;
    }
    /* Spinner text visibility */
    div[data-testid="stSpinner"] p {
        color: #ffffff !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        text-align: center !important;
        letter-spacing: 0.5px !important;
    }
    div[data-testid="stSpinner"] span {
        color: #ffffff !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }
    /* Captions (e.g., under images) need higher contrast on dark background */
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p,
    .stCaption,
    .stCaption p {
        color: rgba(255, 255, 255, 0.87) !important;
    }
    /* Inputs + labels (Streamlit uses BaseWeb under the hood) */
    div[data-testid="stTextInput"] label,
    div[data-testid="stTextInput"] [data-testid="stWidgetLabel"] > label,
    div[data-testid="stTextInput"] [data-testid="stWidgetLabel"] span {
        color: rgba(255, 255, 255, 0.95) !important;
        font-weight: 800 !important;
    }
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextInput"] [data-baseweb="input"] input {
        border-radius: 10px !important;
        min-height: 48px !important;
        background: rgba(7, 8, 16, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.26) !important;
        color: rgba(255, 255, 255, 0.95) !important;
        caret-color: rgba(255, 255, 255, 0.95) !important;
    }
    div[data-testid="stTextInput"] input::placeholder,
    div[data-testid="stTextInput"] [data-baseweb="input"] input::placeholder {
        color: rgba(255, 255, 255, 0.55) !important;
    }
    div[data-testid="stTextInput"] input:hover,
    div[data-testid="stTextInput"] [data-baseweb="input"] input:hover {
        border-color: rgba(168, 85, 247, 0.55) !important;
    }
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextInput"] [data-baseweb="input"] input:focus {
        outline: none !important;
        border-color: rgba(192, 38, 211, 0.75) !important;
        box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.22) !important;
    }
    div[data-testid="stTextInput"] [data-baseweb="input"] > div {
        background: transparent !important;
    }
    .field-error {
        margin-top: 0.35rem;
        margin-bottom: 0.65rem;
        color: rgba(251, 191, 36, 0.98); /* amber */
        font-size: 0.88rem;
        font-weight: 750;
        line-height: 1.25;
    }
    div[data-testid="stButton"] > button {
        border-radius: 8px;
        min-height: 46px;
        font-weight: 800;
        color: var(--ink);
        background: linear-gradient(90deg, rgba(168, 85, 247, 0.88), rgba(192, 38, 211, 0.88));
        border: 1px solid rgba(255, 255, 255, 0.14);
        box-shadow: 0 14px 30px rgba(168, 85, 247, 0.18);
    }
    div[data-testid="stButton"] > button:hover {
        filter: brightness(1.06);
    }
    div[data-testid="stButton"] > button p {
        color: inherit;
        font-size: inherit;
        line-height: 1;
    }
    @media (max-width: 768px) {
        .block-container {
            max-width: 100% !important;
            padding-left: 0.75rem;
            padding-right: 0.75rem;
            padding-top: 1.25rem;
            padding-bottom: 1rem;
        }
        .main {
            padding: 1rem !important;
        }
        .booking-hero {
            margin-bottom: 1rem;
        }
        .booking-title {
            font-size: clamp(1.4rem, 5vw, 2rem) !important;
        }
        .booking-copy {
            font-size: 0.9rem !important;
            margin-top: 0.5rem !important;
        }
        .booking-steps {
            grid-template-columns: 1fr;
            gap: 0.5rem !important;
            margin: 1rem 0 !important;
        }
        .step-pill {
            min-height: 50px;
            padding: 0.65rem 0.75rem;
        }
        .step-text {
            font-size: 0.85rem;
        }
        .booking-layout {
            margin-top: 0.5rem !important;
        }
        .booking-panel {
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .panel-title {
            font-size: 1.1rem;
        }
        .panel-copy {
            font-size: 0.85rem;
            margin-bottom: 1rem !important;
        }
        .amount-row {
            align-items: flex-start;
            flex-direction: column;
            gap: 0.5rem;
            padding: 0.75rem;
            margin-bottom: 0.8rem;
        }
        .amount-label {
            font-size: 0.75rem;
        }
        .amount-value {
            font-size: 1.2rem;
        }
        .quantity-control {
            margin: 0.5rem 0 0.8rem;
            padding: 0.65rem 0.75rem 0.3rem;
        }
        .quantity-title {
            font-size: 0.9rem;
        }
        .quantity-caption {
            font-size: 0.78rem;
        }
        .quantity-value {
            font-size: 1.2rem;
            min-height: 40px;
        }
        .payment-placeholder {
            min-height: 160px;
            padding: 1rem;
        }
        .booking-layout [data-testid="stImage"] {
            max-width: 100% !important;
            padding: 0.5rem;
        }
        .confirmation-shell {
            margin: 1rem auto 0 !important;
            max-width: 100% !important;
        }
        .confirmation-card {
            padding: 1rem;
            border-radius: 6px;
        }
        .confirmation-title {
            font-size: clamp(1.3rem, 4vw, 1.8rem);
        }
        .confirmation-copy {
            font-size: 0.95rem;
            margin-bottom: 0.8rem !important;
        }
        .summary-grid {
            grid-template-columns: 1fr;
            gap: 0.5rem;
        }
        .summary-item {
            padding: 0.7rem;
        }
        .summary-label {
            font-size: 0.7rem;
        }
        .summary-value {
            font-size: 0.95rem;
        }
        .delivery-list {
            gap: 0.5rem;
            margin-top: 0.8rem;
        }
        .delivery-row {
            gap: 0.5rem;
            padding: 0.7rem;
        }
        .delivery-title {
            font-size: 0.95rem;
        }
        .delivery-copy {
            font-size: 0.85rem;
        }
        .delivery-note {
            font-size: 0.85rem;
            padding: 0.7rem;
            margin-top: 0.5rem;
        }
        div[data-testid="stButton"] > button {
            min-height: 42px;
            font-size: 0.95rem;
        }
        div[data-testid="stTextInput"] input {
            min-height: 42px !important;
            font-size: 16px !important;
        }
        .field-error {
            font-size: 0.82rem;
            margin-bottom: 0.5rem;
        }
    }
    @media (max-width: 480px) {
        .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
            padding-top: 1rem;
        }
        .booking-eyebrow {
            font-size: 0.75rem;
            letter-spacing: 0.12em;
        }
        .booking-title {
            font-size: clamp(1.2rem, 5vw, 1.6rem) !important;
            line-height: 1.2 !important;
        }
        .booking-copy {
            font-size: 0.85rem !important;
            max-width: 100% !important;
        }
        .step-pill {
            min-height: 45px;
            padding: 0.5rem 0.6rem;
            gap: 0.4rem;
        }
        .step-index {
            width: 26px !important;
            height: 26px !important;
            font-size: 0.75rem;
            flex: 0 0 26px !important;
        }
        .step-text {
            font-size: 0.8rem;
        }
        .booking-panel {
            padding: 0.8rem;
        }
        .panel-title {
            font-size: 1rem;
            margin-bottom: 0.3rem;
        }
        .panel-copy {
            font-size: 0.8rem;
        }
        .amount-value {
            font-size: 1.1rem;
        }
        .payment-placeholder {
            min-height: 140px;
            padding: 0.8rem;
            border-radius: 6px;
        }
        .confirmation-icon {
            width: 40px !important;
            height: 40px !important;
            font-size: 1.2rem;
        }
        .delivery-status-icon {
            width: 24px !important;
            height: 24px !important;
            flex: 0 0 24px !important;
            font-size: 0.85rem;
        }
        /* Admin tabs mobile styling */
        [data-testid="stTabs"] [role="tab"] {
            font-size: 0.85rem;
            padding: 0.6rem 0.8rem;
        }
        [data-testid="stDataFrame"] {
            font-size: 0.8rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

def ensure_session_state():
    """Initialize session defaults for every Streamlit page entrypoint."""
    defaults = {
        "mode": "Booking",
        "admin_authenticated": False,
        "payment_done": False,
        "booking_details_key": "",
        "ticket_count": 1,
        "booking_submitted": False,
        "booking_delivery_result": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

ensure_session_state()

def init_app():
    """Initialize the application with Google Sheets connection."""
    sheet_url = st.secrets.get("sheet_url")
    if not sheet_url:
        st.error("Sheet URL not found in secrets. Please configure st.secrets with 'sheet_url'.")
        return None
    
    worksheet = get_worksheet(sheet_url)
    if worksheet:
        initialize_sheet(worksheet)
    return worksheet

def parse_ticket_amount(raw_amount) -> float:
    """Parse configured ticket amount into a numeric value."""
    try:
        return float(str(raw_amount).replace(",", "").strip())
    except ValueError:
        return 299.0

def format_amount(amount: float) -> str:
    """Format amounts without unnecessary decimal places."""
    if float(amount).is_integer():
        return str(int(amount))
    return f"{amount:.2f}"

def create_ticket_qr_attachments(ticket_uuids):
    """Create branded PNG ticket attachments for ticket delivery."""
    attachments = []
    template_path_raw = str(st.secrets.get("ticket_template_path", "assets/ticket_logo.jpeg"))
    # Secrets TOML strings treat \t as a tab, so Windows-style paths like
    # "assets\ticket.png" can accidentally become "assets<TAB>icket.png".
    template_path_normalized = (
        template_path_raw.replace("\t", "/").replace("\\", "/").strip()
    )
    template_path = Path(template_path_normalized)
    if not template_path.is_absolute():
        template_path = (Path(__file__).resolve().parent / template_path).resolve()
    template_fit_mode = str(st.secrets.get("ticket_template_fit_mode", "photo_square"))
    template_qr_scale = float(st.secrets.get("ticket_template_qr_scale", 0.27))
    template_qr_center_x = float(st.secrets.get("ticket_template_qr_center_x", 0.5))
    template_qr_center_y = float(st.secrets.get("ticket_template_qr_center_y", 0.39))
    template_qr_padding_scale = float(st.secrets.get("ticket_template_qr_padding_scale", 0.08))
    template_photo_square_inset_scale = float(st.secrets.get("ticket_template_photo_square_inset_scale", 0.04))
    template_photo_square_inset_top_scale = st.secrets.get("ticket_template_photo_square_inset_top_scale", None)
    template_photo_square_offset_y_scale = float(st.secrets.get("ticket_template_photo_square_offset_y_scale", 0.0))
    for index, ticket_uuid in enumerate(ticket_uuids, start=1):
        if template_path.exists():
            ticket_qr = generate_branded_ticket_image(
                ticket_uuid,
                template_path,
                fit_mode=template_fit_mode,
                qr_scale=template_qr_scale,
                qr_center_x=template_qr_center_x,
                qr_center_y=template_qr_center_y,
                qr_padding_scale=template_qr_padding_scale,
                photo_square_inset_scale=template_photo_square_inset_scale,
                photo_square_inset_top_scale=(
                    float(template_photo_square_inset_top_scale)
                    if template_photo_square_inset_top_scale is not None
                    else None
                ),
                photo_square_offset_y_scale=template_photo_square_offset_y_scale,
            )
        else:
            ticket_qr = generate_qr_code(ticket_uuid)
        ticket_qr_bytes = io.BytesIO()
        ticket_qr.save(ticket_qr_bytes, format="PNG")
        attachments.append((f"ticket-{index}-{ticket_uuid[:8]}.png", ticket_qr_bytes.getvalue()))
    return attachments

def normalized_phone_digits(phone: str) -> str:
    """Return only digits from the submitted phone number."""
    return re.sub(r"\D", "", phone or "")

def is_valid_email(email: str) -> bool:
    """Validate a normal email address shape."""
    return bool(re.fullmatch(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email.strip()))

def is_valid_indian_mobile(phone: str) -> bool:
    """Validate Indian mobile numbers with optional +91 prefix."""
    digits = normalized_phone_digits(phone)
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    return bool(re.fullmatch(r"[6-9]\d{9}", digits))

def is_valid_utr(utr_id: str) -> bool:
    """Validate a UTR/transaction reference without accepting punctuation or spaces."""
    clean_utr = (utr_id or "").strip()
    return bool(re.fullmatch(r"[A-Za-z0-9]{8,35}", clean_utr))

def validate_booking_fields(name: str, email: str, phone: str, utr_id: str = ""):
    """Return booking field validation errors."""
    errors = []
    if len((name or "").strip()) < 2:
        errors.append("Full name is required and must be at least 2 characters.")
    if not is_valid_email(email or ""):
        errors.append("Enter a valid email address.")
    if not is_valid_indian_mobile(phone or ""):
        errors.append("Enter a valid 10-digit Indian mobile number, with or without +91.")
    if utr_id and not is_valid_utr(utr_id):
        errors.append("UTR / Transaction ID must be 8 to 35 letters or numbers, without spaces.")
    return errors

def show_booking_delivery_result():
    """Show final post-submit delivery status without the booking form or payment QR."""
    ensure_session_state()
    result = st.session_state["booking_delivery_result"]
    if not result:
        return

    booking_id = result["booking_id"]
    email_status_class = "success" if result["email_sent"] else "warning"
    whatsapp_status_class = "success" if result["whatsapp_sent"] else "warning"
    email_icon = "✓" if result["email_sent"] else "!"
    whatsapp_icon = "✓" if result["whatsapp_sent"] else "!"
    email_copy = (
        "Your ticket QR code has been sent to the email address you entered."
        if result["email_sent"]
        else "Email delivery could not be completed. Your booking is saved, and the team can resend your ticket."
    )
    whatsapp_copy = (
        "Your ticket QR code has also been sent on WhatsApp."
        if result["whatsapp_sent"]
        else "WhatsApp delivery is not complete yet. Your email ticket is enough for entry once approved."
    )

    render_html(
        f"""<div class="confirmation-shell">
<div class="confirmation-card">
<div class="confirmation-icon">✓</div>
<h1 class="confirmation-title">Booking received</h1>
<p class="confirmation-copy">
Your payment details have been submitted. We have generated your ticket QR code
and sent it through the available delivery channels.
</p>

<div class="summary-grid">
<div class="summary-item wide">
<div class="summary-label">Booking ID</div>
<div class="summary-value booking-id-full">{booking_id}</div>
</div>
<div class="summary-item">
<div class="summary-label">Tickets</div>
<div class="summary-value">{result['ticket_count']}</div>
</div>
<div class="summary-item">
<div class="summary-label">Total paid</div>
<div class="summary-value">₹{result['total_amount']}</div>
</div>
</div>

<div class="delivery-list">
<div class="delivery-row {email_status_class}">
<div class="delivery-status-icon">{email_icon}</div>
<div>
<div class="delivery-title">Email ticket</div>
<div class="delivery-copy">{email_copy}</div>
</div>
</div>
<div class="delivery-row {whatsapp_status_class}">
<div class="delivery-status-icon">{whatsapp_icon}</div>
<div>
<div class="delivery-title">WhatsApp ticket</div>
<div class="delivery-copy">{whatsapp_copy}</div>
</div>
</div>
</div>

<div class="delivery-note">
Please keep your ticket QR ready at the entry gate. If WhatsApp delivery is unavailable,
use the email ticket or contact the event team with your booking ID.
</div>
</div>
</div>""",
    )

def booking_mode(worksheet):
    """Booking mode UI for ticket registration."""
    ensure_session_state()
    if st.session_state["booking_submitted"]:
        show_booking_delivery_result()
        return

    ticket_count = int(st.session_state["ticket_count"])
    unit_ticket_amount = 400.0 if ticket_count <= 1 else 350.0
    total_amount = unit_ticket_amount * ticket_count
    total_amount_display = format_amount(total_amount)
    current_details_key = (
        f"{st.session_state.get('booking_name', '').strip()}|"
        f"{st.session_state.get('booking_email', '').strip()}|"
        f"{st.session_state.get('booking_phone', '').strip()}|"
        f"{ticket_count}"
    )
    if current_details_key != st.session_state["booking_details_key"]:
        st.session_state["booking_details_key"] = current_details_key
        st.session_state["payment_done"] = False
    details_ready_for_steps = all(current_details_key.split("|"))

    render_html(
        """
        <div class="booking-hero">
            <div class="booking-eyebrow">The Notebook Concert</div>
            <h1 class="booking-title">Book your ticket</h1>
            <div class="booking-copy">
                Reserve your seat in three quick steps. Enter your details, complete the UPI payment,
                then share the transaction ID so the team can approve your ticket.
            </div>
        </div>
        """,
    )

    step_1_class = "active"
    step_2_class = "active" if details_ready_for_steps or st.session_state["payment_done"] else ""
    step_3_class = "active" if st.session_state["payment_done"] else ""
    render_html(
        f"""
        <div class="booking-steps">
            <div class="step-pill {step_1_class}">
                <span class="step-index">1</span>
                <span class="step-text">Fill details</span>
            </div>
            <div class="step-pill {step_2_class}">
                <span class="step-index">2</span>
                <span class="step-text">Pay with UPI</span>
            </div>
            <div class="step-pill {step_3_class}">
                <span class="step-index">3</span>
                <span class="step-text">Submit UTR</span>
            </div>
        </div>
        """,
    )

    st.markdown('<div class="booking-layout">', unsafe_allow_html=True)
    col1, col2 = st.columns([1.05, 0.95], gap="large", vertical_alignment="top")
    
    with col1:
        with st.container(border=True):
            render_html(
                """
                <h2 class="panel-title">Your details</h2>
                <p class="panel-copy">Use the same mobile number you use for WhatsApp updates.</p>
                """,
            )
            name = st.text_input("Full Name", placeholder="John Doe", key="booking_name")
            name_error_slot = st.empty()
            email = st.text_input("Email Address", placeholder="john@example.com", key="booking_email")
            email_error_slot = st.empty()
            phone = st.text_input("Mobile Number", placeholder="+91 XXXXXXXXXX", key="booking_phone")
            phone_error_slot = st.empty()
            render_html(
                """
                <div class="quantity-control">
                    <div class="quantity-title">Number of tickets</div>
                    <div class="quantity-caption">Adjust this before making payment.</div>
                </div>
                """,
            )
            qty_minus, qty_value, qty_plus = st.columns([1, 2, 1], vertical_alignment="center")
            with qty_minus:
                if st.button("−", use_container_width=True, disabled=ticket_count <= 1):
                    st.session_state["ticket_count"] = max(1, ticket_count - 1)
                    st.session_state["payment_done"] = False
                    st.rerun()
            with qty_value:
                render_html(
                    f'<div class="quantity-value">{ticket_count}</div>',
                )
            with qty_plus:
                if st.button("＋", use_container_width=True):
                    st.session_state["ticket_count"] = min(20, ticket_count + 1)
                    st.session_state["payment_done"] = False
                    st.rerun()
            
            details_key = f"{name.strip()}|{email.strip()}|{phone.strip()}|{ticket_count}"
            if details_key != st.session_state["booking_details_key"]:
                st.session_state["booking_details_key"] = details_key
                st.session_state["payment_done"] = False

            show_field_errors = bool(name.strip() or email.strip() or phone.strip())
            name_error = ""
            if len((name or "").strip()) < 2:
                name_error = "Full name is required and must be at least 2 characters."
            email_error = ""
            if (email or "").strip() and not is_valid_email(email or ""):
                email_error = "Enter a valid email address."
            elif not (email or "").strip():
                email_error = "Email address is required."
            phone_error = ""
            if (phone or "").strip() and not is_valid_indian_mobile(phone or ""):
                phone_error = "Enter a valid 10-digit Indian mobile number, with or without +91."
            elif not (phone or "").strip():
                phone_error = "Mobile number is required."

            if show_field_errors and name_error:
                name_error_slot.markdown(f'<div class="field-error">⚠️ {name_error}</div>', unsafe_allow_html=True)
            else:
                name_error_slot.empty()
            if show_field_errors and email_error:
                email_error_slot.markdown(f'<div class="field-error">⚠️ {email_error}</div>', unsafe_allow_html=True)
            else:
                email_error_slot.empty()
            if show_field_errors and phone_error:
                phone_error_slot.markdown(f'<div class="field-error">⚠️ {phone_error}</div>', unsafe_allow_html=True)
            else:
                phone_error_slot.empty()

            details_entered = not (name_error or email_error or phone_error)
            if st.session_state["payment_done"]:
                render_html(
                    """
                    <div class="payment-done">
                        Payment marked complete. Enter the UTR or transaction ID from your UPI app.
                    </div>
                    """,
                )
                utr_id = st.text_input("UTR / Transaction ID", placeholder="Enter your transaction ID")
                utr_error_slot = st.empty()
                utr_clean = (utr_id or "").strip()
                utr_error = ""
                if not utr_clean:
                    utr_error = "UTR / Transaction ID is required after payment."
                elif not is_valid_utr(utr_clean):
                    utr_error = "UTR / Transaction ID must be 8 to 35 letters or numbers, without spaces."

                # Show error as soon as user starts typing (or when empty after payment done).
                if utr_error:
                    utr_error_slot.markdown(
                        f'<div class="field-error">⚠️ {utr_error}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    utr_error_slot.empty()

                # Only allow submit when UTR is valid.
                submit_btn = st.button(
                    "Submit Booking",
                    type="primary",
                    use_container_width=True,
                    disabled=bool(utr_error) or (not details_entered),
                )
            else:
                utr_id = ""
                submit_btn = False

    with col2:
        with st.container(border=True):
            render_html(
                f"""
                <h2 class="panel-title">Payment</h2>
                <p class="panel-copy">Your QR code appears after the basic details are filled.</p>
                <div class="amount-row">
                    <span class="amount-label">Total for {ticket_count} ticket{'s' if ticket_count > 1 else ''}</span>
                    <span class="amount-value">₹{total_amount_display}</span>
                </div>
                """
                ,
            )
            
            # Show payment QR only after the attendee fills the basic details.
            if details_entered:
                render_html('<div class="payment-card">')
                
                # Get payment details from secrets
                upi_id = st.secrets.get("upi_id", "concert@upi")
                merchant_name = st.secrets.get("merchant_name", "Notebook Concert")
                
                # Create UPI link with amount
                upi_link = f"upi://pay?pa={upi_id}&pn={merchant_name.replace(' ', '%20')}&am={total_amount_display}&tn=Notebook%20Concert%20Ticket"
                
                # Display payment QR code with amount
                payment_qr = generate_qr_code(upi_link)
                payment_qr_bytes = io.BytesIO()
                payment_qr.save(payment_qr_bytes, format='PNG')
                payment_qr_bytes.seek(0)
                st.image(payment_qr_bytes, caption="UPI Payment QR")
                st.caption("Scan the QR code using any UPI app, then return here after payment.")
                if st.button("I have completed the payment", use_container_width=True):
                    st.session_state["payment_done"] = True
                    st.rerun()
                render_html('</div>')
            else:
                render_html(
                    """
                    <div class="payment-placeholder">
                        Fill in your name, email, and mobile number to unlock the payment QR code.
                    </div>
                    """,
                )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if submit_btn:
        with st.spinner("Submitting booking…"):
            # Validation
            validation_errors = validate_booking_fields(name, email, phone, utr_id)
            if not utr_id:
                validation_errors.append("UTR / Transaction ID is required after payment.")

            if validation_errors:
                return

            # Generate UUID and save to Sheets
            booking_id = str(uuid.uuid4())
            ticket_uuids = [str(uuid.uuid4()) for _ in range(ticket_count)]
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            save_results = []
            for index, ticket_uuid in enumerate(ticket_uuids, start=1):
                save_results.append(
                    add_ticket(
                        worksheet,
                        timestamp,
                        name,
                        email,
                        phone,
                        utr_id,
                        ticket_uuid,
                        booking_id=booking_id,
                        ticket_number=index,
                        ticket_count=ticket_count,
                        total_amount=total_amount_display,
                    )
                )

            if all(save_results):
                attachments = create_ticket_qr_attachments(ticket_uuids)
                email_sent, email_message = send_ticket_email(
                    email,
                    name,
                    booking_id,
                    ticket_count,
                    total_amount_display,
                    attachments,
                )
                whatsapp_sent, whatsapp_message = send_ticket_whatsapp(
                    phone,
                    name,
                    booking_id,
                    ticket_count,
                    attachments,
                )

                st.session_state["booking_delivery_result"] = {
                    "booking_id": booking_id,
                    "ticket_count": ticket_count,
                    "total_amount": total_amount_display,
                    "email_sent": email_sent,
                    "email_message": email_message,
                    "whatsapp_sent": whatsapp_sent,
                    "whatsapp_message": whatsapp_message,
                }
                st.session_state["booking_submitted"] = True
                st.rerun()
            else:
                st.error("❌ Failed to save booking. Please try again.")

def admin_mode(worksheet):
    """Admin mode UI for ticket management and QR scanning."""
    st.header("🔐 Admin Panel")
    
    # Admin tabs
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["Approve Tickets", "Scan QR", "All Tickets"])
    
    with admin_tab1:
        st.subheader("Pending Tickets for Approval")
        pending_tickets = get_pending_tickets(worksheet)
        
        if not pending_tickets:
            st.info("✅ No pending tickets at the moment.")
        else:
            for idx, ticket in enumerate(pending_tickets):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{ticket.get('Name')}** - {ticket.get('Email')}")
                    ticket_label = ticket.get("Ticket_Number") or "1"
                    ticket_count_label = ticket.get("Ticket_Count") or "1"
                    amount_label = ticket.get("Total_Amount") or "N/A"
                    st.caption(
                        f"Phone: {ticket.get('Phone')} | UTR: {ticket.get('UTR_ID')} | "
                        f"Ticket {ticket_label}/{ticket_count_label} | Total: ₹{amount_label}"
                    )
                
                with col2:
                    if st.button("✅ Approve", key=f"approve_{idx}_{ticket.get('UUID')}"):
                        if update_ticket_status(worksheet, ticket.get("UUID"), "Valid"):
                            st.success(f"Approved: {ticket.get('Name')}")
                            st.rerun()
                        else:
                            st.error("Failed to approve ticket")
    
    with admin_tab2:
        st.subheader("Scan Ticket QR Code")
        st.write("Take a photo of the QR code to check in the attendee.")
        
        if not PYZBAR_AVAILABLE:
            st.error("⚠️ QR scanning is not available on Windows by default.")
            st.info("""
            **For QR Scanning on Windows**, you have two options:
            
            **Option 1: Manual UUID Entry (Recommended for now)**
            Enter the UUID directly from the QR code display instead of scanning.
            """)
            
            manual_uuid = st.text_input("Enter UUID from ticket:", placeholder="e.g., a1b2c3d4-e5f6-...")
            if manual_uuid:
                ticket = find_ticket_by_uuid(worksheet, manual_uuid)
                
                if ticket:
                    status = ticket.get("Status")
                    if status == "Valid":
                        if update_ticket_status(worksheet, manual_uuid, "Checked In"):
                            st.success(f"✅ Welcome {ticket.get('Name')}! You're checked in.")
                        else:
                            st.error("Failed to check in ticket")
                    elif status == "Checked In":
                        st.warning(f"⚠️ {ticket.get('Name')} is already checked in!")
                    else:
                        st.warning(f"⚠️ Ticket status: {status}. Cannot check in.")
                else:
                    st.error(f"❌ Ticket not found for UUID: {manual_uuid}")
        else:
            camera_input = st.camera_input("Take a photo of the QR code")
            
            if camera_input is not None:
                # Convert camera input to OpenCV format
                img = Image.open(camera_input)
                img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                
                # Decode QR code
                try:
                    decoded_objects = decode(img_cv)
                    
                    if decoded_objects:
                        scanned_uuid = decoded_objects[0].data.decode('utf-8')
                        ticket = find_ticket_by_uuid(worksheet, scanned_uuid)
                        
                        if ticket:
                            status = ticket.get("Status")
                            if status == "Valid":
                                if update_ticket_status(worksheet, scanned_uuid, "Checked In"):
                                    st.success(f"✅ Welcome {ticket.get('Name')}! You're checked in.")
                                else:
                                    st.error("Failed to check in ticket")
                            elif status == "Checked In":
                                st.warning(f"⚠️ {ticket.get('Name')} is already checked in!")
                            else:
                                st.warning(f"⚠️ Ticket status: {status}. Cannot check in.")
                        else:
                            st.error(f"❌ Ticket not found for UUID: {scanned_uuid}")
                    else:
                        st.error("❌ No QR code detected. Please try again.")
                except Exception as e:
                    st.error(f"❌ Error decoding QR code: {str(e)}")
    
    with admin_tab3:
        st.subheader("All Tickets")
        all_tickets = get_all_tickets(worksheet)
        
        if all_tickets:
            df_display = []
            for ticket in all_tickets:
                df_display.append({
                    "Name": ticket.get("Name"),
                    "Email": ticket.get("Email"),
                    "Phone": ticket.get("Phone"),
                    "Ticket": f"{ticket.get('Ticket_Number') or '1'}/{ticket.get('Ticket_Count') or '1'}",
                    "Total": ticket.get("Total_Amount") or "",
                    "Status": ticket.get("Status"),
                    "UUID": ticket.get("UUID")[:8] + "..." if ticket.get("UUID") else "N/A",
                })
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("No tickets found.")

def get_initialized_worksheet():
    """Initialize worksheet and show a user-facing error if setup fails."""
    worksheet = init_app()
    if worksheet is None:
        st.error("Failed to initialize the application. Please check your configuration.")
        return
    return worksheet

def render_booking_page():
    """Render the customer booking page."""
    ensure_session_state()
    worksheet = get_initialized_worksheet()
    if worksheet is None:
        return
    booking_mode(worksheet)

def render_admin_page():
    """Render the protected admin page."""
    ensure_session_state()
    worksheet = get_initialized_worksheet()
    if worksheet is None:
        return

    st.header("🔐 Admin Access")
    admin_password = st.text_input(
        "Admin Password",
        type="password",
        placeholder="Enter admin password",
    )
    correct_password = st.secrets.get("admin_password", "admin123")

    if admin_password == correct_password:
        st.session_state["admin_authenticated"] = True
    elif admin_password:
        st.session_state["admin_authenticated"] = False
        st.error("❌ Incorrect password. Please enter the correct admin password to access this section.")
    else:
        st.session_state["admin_authenticated"] = False
        st.info("Enter the admin password to manage bookings and check-ins.")

    if st.session_state["admin_authenticated"]:
        admin_mode(worksheet)

def render_footer():
    """Render shared footer with contact information."""
    st.divider()
    render_html("""
        <div class="header-contact">
            <div class="header-contact-title">📞 For any Queries reach out to</div>
            <div class="header-contact-phones">
                <div class="header-contact-phone">
                    <span class="header-contact-icon">📱</span>
                    <a href="tel:+919004940265">9004940265</a>
                </div>
                <div class="header-contact-phone">
                    <span class="header-contact-icon">📱</span>
                    <a href="tel:+918899779900">8899779900</a>
                </div>
            </div>
        </div>
    """)
    st.markdown("""
        <div style='text-align: center; color: gray; font-size: 0.8rem; margin-top: 1rem;'>
        🎵 The Notebook Concert - Ticketing System | Built with Streamlit
        </div>
    """, unsafe_allow_html=True)

def main():
    """Main application logic. Root URL defaults to booking."""
    render_booking_page()
    render_footer()

if __name__ == "__main__":
    main()
