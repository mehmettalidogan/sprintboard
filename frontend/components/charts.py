import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from components.styles import (
    C_PRIMARY, C_ACCENT, C_CYAN, C_SUCCESS, C_DANGER,
    C_WARNING, C_BORDER, C_TEXT_2, C_TEXT_3,
    FONT_SANS, FONT_MONO,
)

_BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family=FONT_SANS, color=C_PRIMARY, size=13),
    margin=dict(l=0, r=0, t=32, b=0),
    hoverlabel=dict(
        bgcolor="#0F172A",
        font_color="#F1F5F9",
        font_family=FONT_SANS,
        bordercolor="#1E293B",
    ),
)


def score_gauge(value: float, title: str, color: str) -> go.Figure:
    """0-100 arası skor için gösterge ibresi."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number=dict(
                font=dict(family=FONT_MONO, size=40, color=color),
                suffix="",
            ),
            gauge=dict(
                axis=dict(
                    range=[0, 100],
                    tickwidth=0,
                    tickcolor="rgba(0,0,0,0)",
                    tickfont=dict(color=C_TEXT_3, size=10, family=FONT_MONO),
                    nticks=6,
                ),
                bar=dict(color=color, thickness=0.7),
                bgcolor="#F1F5F9",
                borderwidth=0,
                steps=[
                    dict(range=[0, 50],  color="#FEE2E2"),
                    dict(range=[50, 75], color="#FEF3C7"),
                    dict(range=[75, 100], color="#D1FAE5"),
                ],
                threshold=dict(
                    line=dict(color=C_PRIMARY, width=2),
                    thickness=0.8,
                    value=value,
                ),
            ),
            title=dict(
                text=title,
                font=dict(size=13, color=C_TEXT_2, family=FONT_SANS),
            ),
        )
    )
    fig.update_layout(**dict(_BASE_LAYOUT, height=220, margin=dict(l=16, r=16, t=24, b=8)))
    return fig


def workload_pie(member_performance: list[dict]) -> go.Figure:
    """Takım üyelerinin iş payı pasta grafiği."""
    labels = [m["github_login"] for m in member_performance]
    values = [m["workload_share"] for m in member_performance]
    _palette = [
        C_ACCENT, C_CYAN, C_SUCCESS, C_WARNING,
        "#8B5CF6", "#EC4899", "#F97316", "#14B8A6",
        "#F43F5E", "#A78BFA", "#FBBF24", "#34D399",
    ]
    colors = [_palette[i % len(_palette)] for i in range(len(labels))]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
            textfont=dict(family=FONT_SANS, size=12),
            hovertemplate="<b>%{label}</b><br>İş Payı: %{percent}<extra></extra>",
        )
    )
    fig.update_layout(
        **_BASE_LAYOUT,
        height=260,
        showlegend=True,
        legend=dict(
            orientation="v",
            x=1.02,
            y=0.5,
            font=dict(family=FONT_SANS, size=12, color=C_PRIMARY),
        ),
        annotations=[
            dict(
                text="İş Payı<br>Dağılımı",
                x=0.5, y=0.5,
                font=dict(size=12, color=C_TEXT_2, family=FONT_SANS),
                showarrow=False,
            )
        ],
    )
    return fig


from plotly.subplots import make_subplots

def member_bar(member_performance: list[dict]) -> go.Figure:
    """Üye başına commit / ekleme / silme karşılaştırması."""
    df = pd.DataFrame(member_performance).sort_values("total_additions", ascending=True)

    fig = make_subplots(
        rows=1, cols=2, 
        shared_yaxes=True, 
        horizontal_spacing=0.05,
        column_widths=[0.3, 0.7],
        subplot_titles=("Commit Sayısı", "Satır Katkısı (+/-)")
    )

    fig.add_trace(go.Bar(
        y=df["github_login"],
        x=df["total_commits"],
        name="Commit",
        orientation="h",
        marker=dict(color=C_ACCENT, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>%{x} commit<extra></extra>",
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        y=df["github_login"],
        x=df["total_additions"],
        name="Ekleme (+)",
        orientation="h",
        marker=dict(color=C_SUCCESS, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>+%{x} satır<extra></extra>",
    ), row=1, col=2)
    fig.add_trace(go.Bar(
        y=df["github_login"],
        x=df["total_deletions"],
        name="Silme (-)",
        orientation="h",
        marker=dict(color=C_DANGER, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>-%{x} satır<extra></extra>",
    ), row=1, col=2)

    fig.update_layout(
        **_BASE_LAYOUT,
        barmode="group",
        height=max(220, len(df) * 70),
        legend=dict(
            orientation="h",
            x=0, y=1.15,
            font=dict(family=FONT_SANS, size=12),
        ),
    )
    fig.update_xaxes(showgrid=True, gridcolor=C_BORDER, zeroline=False, tickfont=dict(family=FONT_MONO, size=11, color=C_TEXT_2))
    fig.update_yaxes(showgrid=False, tickfont=dict(family=FONT_SANS, size=12, color=C_PRIMARY))
    
    # Subplot başlıkları için font ayarı
    for annotation in fig['layout']['annotations']:
        annotation['font'] = dict(size=12, color=C_TEXT_2, family=FONT_SANS)
        
    return fig


def active_days_bar(member_performance: list[dict], total_working_days: int) -> go.Figure:
    """Aktif gün sayısı — toplam çalışma günüyle karşılaştırmalı."""
    df = pd.DataFrame(member_performance).sort_values("active_days", ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["github_login"],
        y=df["active_days"],
        name="Aktif Gün",
        marker=dict(color=C_CYAN, line=dict(width=0), opacity=0.9),
        hovertemplate="<b>%{x}</b><br>%{y} aktif gün<extra></extra>",
    ))
    fig.add_hline(
        y=total_working_days,
        line_dash="dot",
        line_color=C_TEXT_3,
        annotation_text=f"Sprint: {total_working_days} gün",
        annotation_font=dict(size=11, color=C_TEXT_2, family=FONT_SANS),
    )
    fig.update_layout(
        **_BASE_LAYOUT,
        height=220,
        xaxis=dict(showgrid=False, tickfont=dict(family=FONT_SANS, size=12, color=C_PRIMARY)),
        yaxis=dict(
            showgrid=True,
            gridcolor=C_BORDER,
            zeroline=False,
            tickfont=dict(family=FONT_MONO, size=11, color=C_TEXT_2),
        ),
        showlegend=False,
    )
    return fig
