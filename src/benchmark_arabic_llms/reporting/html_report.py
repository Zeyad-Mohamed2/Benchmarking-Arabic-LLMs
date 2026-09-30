"""
Standalone Interactive HTML & PDF-Ready Report Generator.
Generates a self-contained, publication-grade executive HTML report
with offline styles, SVG radar charts, KPI scorecards, detailed sample analysis,
and print styles optimized for saving as a PDF directly from the browser.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import math


def generate_html_report(
    model_results: Dict[str, Any],
    task: str,
    output_dir: Path | str,
    detailed_samples: Optional[List[Dict[str, Any]]] = None,
) -> Path:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = out_path / f"{task}_report_{timestamp}.html"

    # Compute high-level KPIs
    total_examples = 0
    total_errors = 0
    best_model = "N/A"
    best_score = -1.0
    models_list = list(model_results.keys())

    metrics_set = set()
    for m_name, m_data in model_results.items():
        stats = m_data.get("stats", {})
        scores = m_data.get("scores", {})
        total_examples += stats.get("n_examples", 0)
        total_errors += stats.get("n_errors", 0)

        primary = (
            scores.get("Accuracy")
            or scores.get("accuracy")
            or scores.get("ROUGEL")
            or scores.get("rougeL")
            or scores.get("F1")
            or scores.get("EM")
            or 0.0
        )
        if isinstance(primary, (int, float)) and primary > best_score:
            best_score = primary
            best_model = m_name.replace(":free", "")

        for k, v in scores.items():
            if isinstance(v, (int, float)) and not math.isnan(v):
                metrics_set.add(k)

    success_rate = ((total_examples - total_errors) / max(total_examples, 1)) * 100
    sorted_metrics = sorted(list(metrics_set))

    # Generate SVG radar chart
    radar_svg = _generate_radar_svg(model_results, sorted_metrics)

    # Build rows for metrics table
    table_rows_html = ""
    for idx, (m_name, m_data) in enumerate(model_results.items()):
        scores = m_data.get("scores", {})
        stats = m_data.get("stats", {})
        n_ex = stats.get("n_examples", 0)
        n_err = stats.get("n_errors", 0)
        rate = ((n_ex - n_err) / max(n_ex, 1)) * 100

        rank_badge = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else f"#{idx+1}"

        score_cells = "".join(
            f'<td class="metric-cell">{scores.get(m, 0.0):.4f}</td>' if isinstance(scores.get(m), (int, float))
            else f'<td class="metric-cell text-muted">-</td>'
            for m in sorted_metrics
        )

        table_rows_html += f"""
        <tr>
            <td class="rank-cell">{rank_badge}</td>
            <td class="model-name"><strong>{m_name.replace(':free', '')}</strong></td>
            <td>{n_ex}</td>
            <td>{n_err}</td>
            <td>{rate:.1f}%</td>
            {score_cells}
        </tr>
        """

    # Build detailed samples if available
    samples_section_html = ""
    if detailed_samples and len(detailed_samples) > 0:
        samples_rows = ""
        for sample in detailed_samples[:20]:  # Highlight up to 20 samples
            ex_num = sample.get("Example_Number", "-")
            m_name = str(sample.get("Model", "")).replace(":free", "")
            inp = sample.get("Input_Text", sample.get("text", "-"))
            pred = sample.get("Model_Prediction", sample.get("prediction", "-"))
            ref = sample.get("Expected_Answer", sample.get("answer", sample.get("summary", "-")))
            is_match = sample.get("Exact_Match", False)
            match_badge = (
                '<span class="badge badge-success">MATCH</span>'
                if is_match
                else '<span class="badge badge-warning">DIFF</span>'
            )

            samples_rows += f"""
            <tr>
                <td><strong>#{ex_num}</strong></td>
                <td><span class="badge badge-model">{m_name}</span></td>
                <td class="arabic-text">{inp}</td>
                <td class="arabic-text prediction-cell">{pred}</td>
                <td class="arabic-text reference-cell">{ref}</td>
                <td>{match_badge}</td>
            </tr>
            """

        samples_section_html = f"""
        <div class="section-card page-break-before">
            <h3 class="section-title">🔍 Detailed Sample Inspector (First {min(len(detailed_samples), 20)} Examples)</h3>
            <p class="section-desc">Sample prompt outputs, ground-truth targets, and match classifications.</p>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Model</th>
                            <th>Prompt / Input Context</th>
                            <th>Model Output</th>
                            <th>Expected Target</th>
                            <th>Match</th>
                        </tr>
                    </thead>
                    <tbody>
                        {samples_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

    headers_html = "".join(f"<th>{m}</th>" for m in sorted_metrics)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Benchmark Report — {task.replace('_', ' ').title()}</title>
    <style>
        :root {{
            --bg: #0b0f19;
            --surface: #111827;
            --card: #1f2937;
            --border: #374151;
            --teal: #32C4B7;
            --text: #f3f4f6;
            --text-muted: #9ca3af;
            --success: #10b981;
            --warning: #f59e0b;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}
        body {{
            background-color: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 24px;
            margin-bottom: 32px;
        }}
        .header-title h1 {{
            font-size: 26px;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: -0.5px;
        }}
        .header-title p {{
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 4px;
        }}
        .header-actions {{
            display: flex;
            gap: 12px;
        }}
        .btn {{
            background: var(--teal);
            color: #0b0f19;
            font-weight: 700;
            font-size: 13px;
            border: none;
            padding: 10px 18px;
            border-radius: 8px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
            text-decoration: none;
        }}
        .btn:hover {{
            background: #2aa69b;
        }}
        .btn-outline {{
            background: transparent;
            color: var(--text);
            border: 1px solid var(--border);
        }}
        .btn-outline:hover {{
            background: var(--card);
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 32px;
        }}
        .kpi-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}
        .kpi-label {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            margin-bottom: 6px;
        }}
        .kpi-value {{
            font-size: 24px;
            font-weight: 800;
            color: #ffffff;
        }}
        .kpi-subtext {{
            font-size: 12px;
            color: var(--teal);
            margin-top: 4px;
        }}
        .section-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 28px;
            margin-bottom: 32px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.25);
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 6px;
        }}
        .section-desc {{
            font-size: 13px;
            color: var(--text-muted);
            margin-bottom: 20px;
        }}
        .table-container {{
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            text-align: left;
        }}
        th {{
            background: rgba(31, 41, 55, 0.6);
            color: var(--text-muted);
            text-transform: uppercase;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
        }}
        td {{
            padding: 14px 16px;
            border-bottom: 1px solid rgba(55, 65, 81, 0.5);
            vertical-align: top;
        }}
        tr:hover td {{
            background: rgba(31, 41, 55, 0.4);
        }}
        .rank-cell {{
            font-size: 16px;
            text-align: center;
            width: 40px;
        }}
        .metric-cell {{
            font-family: monospace;
            font-weight: 600;
            color: var(--teal);
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .badge-success {{
            background: rgba(16, 185, 129, 0.2);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.4);
        }}
        .badge-warning {{
            background: rgba(245, 158, 11, 0.2);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.4);
        }}
        .badge-model {{
            background: var(--card);
            color: #e5e7eb;
            border: 1px solid var(--border);
        }}
        .arabic-text {{
            direction: rtl;
            text-align: right;
            font-size: 13px;
            line-height: 1.7;
            max-width: 320px;
        }}
        .prediction-cell {{
            color: #38bdf8;
        }}
        .reference-cell {{
            color: #a78bfa;
        }}
        .radar-box {{
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            overflow-x: auto;
        }}
        .footer {{
            text-align: center;
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
        }}

        /* Print / PDF Mode */
        @media print {{
            body {{
                background: #ffffff !important;
                color: #000000 !important;
                padding: 0 !important;
            }}
            .header-actions, .no-print {{
                display: none !important;
            }}
            .section-card, .kpi-card {{
                border: 1px solid #d1d5db !important;
                background: #ffffff !important;
                box-shadow: none !important;
                color: #000000 !important;
            }}
            .header-title h1, .section-title, .kpi-value {{
                color: #000000 !important;
            }}
            th {{
                background: #f3f4f6 !important;
                color: #374151 !important;
            }}
            td {{
                color: #1f2937 !important;
                border-bottom: 1px solid #e5e7eb !important;
            }}
            .metric-cell {{
                color: #0d9488 !important;
            }}
            .page-break-before {{
                page-break-before: always;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <div class="header-title">
                <h1>Framework for Open-Source Multilingual Large Language Models</h1>
                <p>Task Evaluation Report: <strong>{task.replace('_', ' ').title()}</strong> • Generated on {datetime.now().strftime("%B %d, %Y at %H:%M")}</p>
            </div>
            <div class="header-actions no-print">
                <button onclick="window.print()" class="btn">
                    🖨️ Print / Save as PDF
                </button>
            </div>
        </header>

        <!-- KPI Scorecards -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Top Performing Model</div>
                <div class="kpi-value">{best_model[:22]}</div>
                <div class="kpi-subtext">🏆 Highest composite score</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Best Primary Score</div>
                <div class="kpi-value">{f"{best_score:.4f}" if best_score >= 0 else "N/A"}</div>
                <div class="kpi-subtext">🎯 Normalized evaluation target</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">API Reliability Rate</div>
                <div class="kpi-value">{success_rate:.1f}%</div>
                <div class="kpi-subtext">⚡ {total_examples - total_errors}/{total_examples} successful inferences</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Models Benchmarked</div>
                <div class="kpi-value">{len(models_list)}</div>
                <div class="kpi-subtext">Across {total_examples} total inferences</div>
            </div>
        </div>

        <!-- Metrics Comparison Table -->
        <div class="section-card">
            <h3 class="section-title">📊 Comparative Model Performance</h3>
            <p class="section-desc">Unified benchmark evaluation scores across all assessed dimensions.</p>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Model Architecture</th>
                            <th>Samples</th>
                            <th>Errors</th>
                            <th>API Success</th>
                            {headers_html}
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows_html}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Radar Analysis -->
        <div class="section-card">
            <h3 class="section-title">🕸️ Normalized Multi-Metric Radar Analysis</h3>
            <p class="section-desc">Multi-dimensional polygon footprint comparing models across all normalized axes.</p>
            <div class="radar-box">
                {radar_svg}
            </div>
        </div>

        <!-- Detailed Samples -->
        {samples_section_html}

        <!-- Footer -->
        <footer class="footer">
            <p>Faculty of Computers and Artificial Intelligence, Fayoum University • Benchmarking Arabic LLMs Research Framework</p>
        </footer>
    </div>
</body>
</html>
    """

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[OK] Standalone HTML & PDF-ready report exported: {report_file}")
    return report_file


def _generate_radar_svg(model_results: Dict[str, Any], metrics: List[str]) -> str:
    """Generate inline SVG radar chart matching the web UI aesthetics."""
    if len(metrics) < 3:
        return "<p class='text-muted'>Radar profile requires at least 3 distinct evaluation metrics.</p>"

    metrics = metrics[:8]  # cap at 8 axes
    size = 440
    center = size / 2
    radius = size * 0.36
    num_metrics = len(metrics)
    angle_step = (math.pi * 2) / num_metrics

    palette = [
        {"stroke": "#32C4B7", "fill": "rgba(50, 196, 183, 0.25)"},
        {"stroke": "#818cf8", "fill": "rgba(129, 140, 248, 0.25)"},
        {"stroke": "#f472b6", "fill": "rgba(244, 114, 182, 0.25)"},
        {"stroke": "#fbbf24", "fill": "rgba(251, 191, 36, 0.25)"},
    ]

    rings = [0.25, 0.5, 0.75, 1.0]
    rings_svg = ""
    for r_val in rings:
        r = r_val * radius
        pts = " ".join(
            f"{center + r * math.cos(i * angle_step - math.pi / 2)},{center + r * math.sin(i * angle_step - math.pi / 2)}"
            for i in range(num_metrics)
        )
        rings_svg += f'<polygon points="{pts}" fill="none" stroke="#374151" stroke-width="1" stroke-dasharray="3,3" />'
        rings_svg += f'<text x="{center + 5}" y="{center - r + 12}" fill="#6b7280" font-size="10" font-family="monospace">{r_val:.2f}</text>'

    axes_svg = ""
    for i, metric in enumerate(metrics):
        angle = i * angle_step - math.pi / 2
        end_x = center + radius * math.cos(angle)
        end_y = center + radius * math.sin(angle)
        label_dist = radius + 22
        lbl_x = center + label_dist * math.cos(angle)
        lbl_y = center + label_dist * math.sin(angle)

        anchor = "middle"
        if math.cos(angle) > 0.3:
            anchor = "start"
        elif math.cos(angle) < -0.3:
            anchor = "end"

        axes_svg += f'<line x1="{center}" y1="{center}" x2="{end_x}" y2="{end_y}" stroke="#374151" stroke-width="1" />'
        axes_svg += f'<text x="{lbl_x}" y="{lbl_y + 4}" fill="#9ca3af" font-size="11" font-weight="600" text-anchor="{anchor}">{metric}</text>'

    polygons_svg = ""
    for idx, (m_name, m_data) in enumerate(model_results.items()):
        color = palette[idx % len(palette)]
        scores = m_data.get("scores", {})

        coords = []
        for i, metric in enumerate(metrics):
            val = float(scores.get(metric, 0.0))
            clamped = max(0.0, min(1.0, val))
            r = clamped * radius
            angle = i * angle_step - math.pi / 2
            coords.append(f"{center + r * math.cos(angle)},{center + r * math.sin(angle)}")

        pts_str = " ".join(coords)
        polygons_svg += f'<polygon points="{pts_str}" fill="{color["fill"]}" stroke="{color["stroke"]}" stroke-width="2.5" />'

    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="overflow: visible;">
        {rings_svg}
        {axes_svg}
        {polygons_svg}
    </svg>
    """
