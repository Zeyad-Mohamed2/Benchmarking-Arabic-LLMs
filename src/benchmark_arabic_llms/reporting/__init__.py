"""Reporting and styling modules for benchmark outputs."""
from .excel_styler import style_existing_workbook
from .html_report import generate_html_report

__all__ = ["style_existing_workbook", "generate_html_report"]
