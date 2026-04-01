import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.graph_objects as go
import pandas as pd
import os

# ── Load CSVs ────────────────────────────────────────────────────────────────
# Place all CSVs in the same folder as this script
BASE = os.path.dirname(os.path.abspath(__file__))

leaderboard  = pd.read_csv(os.path.join(BASE, 'leaderboard.csv'))
industry     = pd.read_csv(os.path.join(BASE, 'industry_breakdown.csv'))
stage        = pd.read_csv(os.path.join(BASE, 'funding_stage_analysis.csv'))
city         = pd.read_csv(os.path.join(BASE, 'eff_by_city.csv'))
corr         = pd.read_csv(os.path.join(BASE, 'efficiency_corr.csv'))

# ── Clean up whitespace in string columns ─────────────────────────────────────
for df in [leaderboard, industry, stage, city, corr]:
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].str.strip()

# ── Sort stage in a logical order ─────────────────────────────────────────────
ROUND_ORDER = ['Seed Only', 'Venture Only', 'Series A', 'Series B', 'Series C', 'Series D+']
stage['highest_round'] = stage['highest_round'].str.replace(r'^\d+\.\s*', '', regex=True)
stage = stage[stage['highest_round'] != 'No Round Data'].copy()
stage['highest_round'] = pd.Categorical(
    stage['highest_round'],
    categories=[r for r in ROUND_ORDER if r in stage['highest_round'].values],
    ordered=True
)
stage = stage.sort_values('highest_round')

# ── Color palette ─────────────────────────────────────────────────────────────
STATUS_COLORS = {
    'acquired':  '#00E5A0',
    'operating': '#4DA8FF',
    'closed':    '#FF4D6D',
    'ipo':       '#FFD700',
}
BG      = '#0A0E1A'
CARD_BG = '#111827'
BORDER  = '#1E2D45'
TEXT    = '#E8EEF7'
SUBTEXT = '#6B7FA3'
ACCENT  = '#00E5A0'
ACCENT2 = '#4DA8FF'
FONT    = "'Inter', sans-serif"

PLOT_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family=FONT, color=TEXT, size=11),
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
    yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
)

# ── Dropdown options ──────────────────────────────────────────────────────────
markets  = sorted(industry['market'].dropna().unique().tolist())
statuses = sorted(leaderboard['status'].dropna().unique().tolist())

# ── Helpers ───────────────────────────────────────────────────────────────────
def card(children, style=None):
    base = {
        'background': CARD_BG, 'border': f'1px solid {BORDER}',
        'borderRadius': '12px', 'padding': '24px', 'marginBottom': '20px',
    }
    if style:
        base.update(style)
    return html.Div(children, style=base)

def label(text):
    return html.P(text, style={
        'color': SUBTEXT, 'fontSize': '11px', 'letterSpacing': '1.5px',
        'textTransform': 'uppercase', 'marginBottom': '8px', 'fontFamily': FONT,
        'fontWeight': '600',
    })

def stat_card(title, value, color=ACCENT):
    return html.Div([
        html.P(title, style={
            'color': SUBTEXT, 'fontSize': '10px', 'letterSpacing': '2px',
            'textTransform': 'uppercase', 'margin': '0 0 8px', 'fontFamily': FONT
        }),
        html.H2(value, style={
            'color': color, 'fontSize': '22px', 'margin': '0',
            'fontFamily': FONT, 'fontWeight': '700',
            'wordBreak': 'break-word', 'lineHeight': '1.25',
        })
    ], style={
        'background': CARD_BG, 'border': f'1px solid {BORDER}',
        'borderRadius': '12px', 'padding': '20px 24px',
        'borderTop': f'3px solid {color}'
    })

# ── App ───────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__)
server = app.server  
app.title = "Startup Efficiency Analyzer"

app.layout = html.Div(style={'backgroundColor': BG, 'minHeight': '100vh',
                              'fontFamily': FONT, 'color': TEXT}, children=[

    html.Link(rel='stylesheet',
              href='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'),

    # ── Header ────────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Span('◈', style={'fontSize': '26px', 'color': ACCENT, 'marginRight': '12px'}),
            html.Div([
                html.H1('STARTUP EFFICIENCY ANALYZER', style={
                    'margin': '0', 'fontSize': '18px', 'letterSpacing': '4px',
                    'color': TEXT, 'fontWeight': '700'
                }),
                html.P('Capital efficiency intelligence · US venture-backed startups · Crunchbase 2013',
                       style={'margin': '2px 0 0', 'color': SUBTEXT,
                              'fontSize': '11px', 'letterSpacing': '1px'}),
            ])
        ], style={'display': 'flex', 'alignItems': 'center'}),
        html.Span(f'{len(leaderboard):,}+ companies analyzed', style={
            'color': ACCENT, 'fontSize': '11px', 'letterSpacing': '1px',
            'background': '#00E5A015', 'padding': '6px 14px',
            'borderRadius': '20px', 'border': f'1px solid {ACCENT}44'
        })
    ], style={
        'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
        'padding': '18px 40px', 'borderBottom': f'1px solid {BORDER}',
        'background': f'linear-gradient(90deg, {CARD_BG} 0%, #0D1526 100%)',
        'position': 'sticky', 'top': '0', 'zIndex': '100',
    }),

    html.Div(style={'padding': '28px 40px'}, children=[

        # ── Filters ───────────────────────────────────────────────────────────
        card([
            html.Div([
                html.Div([
                    html.P('Filter by Industry', style={
                        'color': TEXT, 'fontSize': '12px', 'fontWeight': '600',
                        'marginBottom': '8px', 'fontFamily': FONT,
                    }),
                    dcc.Dropdown(
                        id='market-filter',
                        options=[{'label': 'All Industries', 'value': 'ALL'}] +
                                [{'label': m, 'value': m} for m in markets],
                        value='ALL', clearable=False,
                        className='dark-dropdown',
                        style={'fontFamily': FONT},
                    )
                ], style={'flex': '1', 'marginRight': '24px'}),

                html.Div([
                    html.P('Filter by Status', style={
                        'color': TEXT, 'fontSize': '12px', 'fontWeight': '600',
                        'marginBottom': '8px', 'fontFamily': FONT,
                    }),
                    dcc.Dropdown(
                        id='status-filter',
                        options=[{'label': 'All Statuses', 'value': 'ALL'}] +
                                [{'label': s.title(), 'value': s} for s in statuses],
                        value='ALL', clearable=False,
                        className='dark-dropdown',
                        style={'fontFamily': FONT},
                    )
                ], style={'flex': '1', 'marginRight': '24px'}),

                html.Div([
                    html.P('Min Efficiency Score', style={
                        'color': TEXT, 'fontSize': '12px', 'fontWeight': '600',
                        'marginBottom': '8px', 'fontFamily': FONT,
                    }),
                    dcc.Slider(
                        id='score-filter', min=0, max=100, step=5, value=0,
                        marks={0:   {'label': '0',   'style': {'color': SUBTEXT}},
                               50:  {'label': '50',  'style': {'color': SUBTEXT}},
                               100: {'label': '100', 'style': {'color': SUBTEXT}}},
                        tooltip={'placement': 'bottom', 'always_visible': True}
                    )
                ], style={'flex': '1.5'}),
            ], style={'display': 'flex', 'alignItems': 'flex-end'})
        ], style={'padding': '20px 24px', 'marginBottom': '20px'}),

        # ── KPI Row ───────────────────────────────────────────────────────────
        html.Div(id='kpi-row', style={
            'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)',
            'gap': '16px', 'marginBottom': '24px'
        }),

        # ── Row 1: Leaderboard + Industry ─────────────────────────────────────
        html.Div([
            html.Div([card([
                label('Top Companies — Efficiency Leaderboard'),
                dcc.Graph(id='leaderboard-chart', config={'displayModeBar': False},
                          style={'height': '500px'})
            ])], style={'flex': '1.2', 'marginRight': '20px'}),

            html.Div([card([
                label('Avg Efficiency Score by Industry'),
                dcc.Graph(id='industry-chart', config={'displayModeBar': False},
                          style={'height': '500px'})
            ])], style={'flex': '1'}),
        ], style={'display': 'flex'}),

        # ── Row 2: Stage + Correlation ────────────────────────────────────────
        html.Div([
            html.Div([card([
                label('Efficiency by Highest Funding Round Reached'),
                dcc.Graph(id='stage-chart', config={'displayModeBar': False},
                          style={'height': '380px'})
            ])], style={'flex': '1', 'marginRight': '20px'}),

            html.Div([card([
                label('Does More Funding = More Efficiency?'),
                dcc.Graph(id='corr-chart', config={'displayModeBar': False},
                          style={'height': '380px'})
            ])], style={'flex': '1'}),
        ], style={'display': 'flex'}),

        # ── Row 3: City ───────────────────────────────────────────────────────
        card([
            label('Top Cities by Average Efficiency Score'),
            dcc.Graph(id='city-chart', config={'displayModeBar': False},
                      style={'height': '360px'})
        ]),

        # ── Row 4: Table ──────────────────────────────────────────────────────
        card([
            label('Full Leaderboard Table — Sortable & Filterable'),
            html.Div(id='data-table')
        ]),
    ]),

    # Footer
    html.Div(
        html.P('Startup Efficiency Analyzer  ·  Python · Pandas · SQLite · Plotly Dash  ·  Data: Crunchbase 2013',
               style={'color': SUBTEXT, 'fontSize': '11px', 'margin': '0',
                      'textAlign': 'center', 'letterSpacing': '1px'}),
        style={'padding': '20px', 'borderTop': f'1px solid {BORDER}'}
    ),
])


# ── Callbacks ─────────────────────────────────────────────────────────────────
@app.callback(
    Output('kpi-row', 'children'),
    Output('leaderboard-chart', 'figure'),
    Output('industry-chart', 'figure'),
    Output('stage-chart', 'figure'),
    Output('corr-chart', 'figure'),
    Output('city-chart', 'figure'),
    Output('data-table', 'children'),
    Input('market-filter', 'value'),
    Input('status-filter', 'value'),
    Input('score-filter', 'value'),
)
def update_all(market, status, min_score):

    # ── Filter leaderboard (only chart that responds to filters) ──────────────
    df = leaderboard.copy()
    if market != 'ALL':
        df = df[df['market'] == market]
    if status != 'ALL':
        df = df[df['status'] == status]
    df = df[df['efficiency_score'] >= min_score]

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total     = len(df)
    avg_score = df['efficiency_score'].mean() if total > 0 else 0
    pct_acq   = (df['status'] == 'acquired').sum() / max(total, 1) * 100
    top_mkt   = (df.groupby('market')['efficiency_score'].mean().idxmax()
                 if total > 0 else '—')

    kpis = [
        stat_card('Filtered Companies', f'{total:,}',       ACCENT),
        stat_card('Avg Efficiency',     f'{avg_score:.1f}', ACCENT2),
        stat_card('Acquisition Rate',   f'{pct_acq:.1f}%',  '#FFD700'),
        stat_card('Top Industry',       str(top_mkt),       '#FF6B9D'),
    ]

    # ── Leaderboard ───────────────────────────────────────────────────────────
    top = df.nlargest(20, 'efficiency_score').sort_values('efficiency_score')
    colors = [STATUS_COLORS.get(s, SUBTEXT) for s in top['status']]
    fig_leader = go.Figure(go.Bar(
        x=top['efficiency_score'], y=top['name'], orientation='h',
        marker=dict(color=colors, line=dict(width=0)),
        text=top['status'].str.title(),
        textposition='inside', textfont=dict(size=10, color='white'),
        hovertemplate='<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>'
    ))
    fig_leader.update_layout(**PLOT_LAYOUT)
    fig_leader.update_xaxes(title_text='Efficiency Score', range=[0, 105])
    fig_leader.update_yaxes(tickfont=dict(size=10))

    # ── Industry (unfiltered — shows full picture) ────────────────────────────
    ind = industry.nlargest(15, 'avg_efficiency_score').sort_values('avg_efficiency_score')
    fig_ind = go.Figure(go.Bar(
        x=ind['avg_efficiency_score'], y=ind['market'], orientation='h',
        marker=dict(
            color=ind['avg_efficiency_score'],
            colorscale=[[0, '#1E2D45'], [1, ACCENT]],
            line=dict(width=0)
        ),
        text=ind['company_count'].apply(lambda x: f'{x} cos'),
        textposition='inside', textfont=dict(size=9, color='white'),
        hovertemplate='<b>%{y}</b><br>Avg Score: %{x:.1f}<br>%{text}<extra></extra>'
    ))
    fig_ind.update_layout(**PLOT_LAYOUT)
    fig_ind.update_xaxes(title_text='Avg Efficiency Score')
    fig_ind.update_yaxes(tickfont=dict(size=10))

    # ── Funding stage ─────────────────────────────────────────────────────────
    fig_stage = go.Figure()
    fig_stage.add_trace(go.Bar(
        x=stage['highest_round'].astype(str),
        y=stage['avg_efficiency'],
        name='Avg Efficiency',
        marker=dict(color=ACCENT2, opacity=0.85, line=dict(width=0)),
        hovertemplate='<b>%{x}</b><br>Avg Score: %{y:.1f}<extra></extra>'
    ))
    fig_stage.add_trace(go.Scatter(
        x=stage['highest_round'].astype(str),
        y=stage['company_count'],
        name='Company Count', yaxis='y2',
        mode='lines+markers',
        line=dict(color='#FFD700', width=2),
        marker=dict(size=7, color='#FFD700'),
        hovertemplate='%{y} companies<extra></extra>'
    ))
    stage_layout = {k: v for k, v in PLOT_LAYOUT.items() if k != 'yaxis'}
    fig_stage.update_layout(
        **stage_layout,
        yaxis=dict(title='Avg Efficiency Score', gridcolor=BORDER, zerolinecolor=BORDER),
        yaxis2=dict(title='Company Count', overlaying='y', side='right',
                    gridcolor='rgba(0,0,0,0)', zerolinecolor='rgba(0,0,0,0)'),
        legend=dict(orientation='h', y=1.1, font=dict(size=10)),
    )

    # ── Correlation ───────────────────────────────────────────────────────────
    fig_corr = go.Figure(go.Bar(
        x=corr['funding_percentile'],
        y=corr['avg_efficiency'],
        marker=dict(
            color=corr['avg_efficiency'],
            colorscale=[[0, '#1E2D45'], [0.5, ACCENT2], [1, ACCENT]],
            line=dict(width=0)
        ),
        text=corr['avg_efficiency'].round(1),
        textposition='outside', textfont=dict(size=10, color=TEXT),
        hovertemplate='<b>%{x}</b><br>Avg Efficiency: %{y:.2f}<extra></extra>'
    ))
    corr_layout = {k: v for k, v in PLOT_LAYOUT.items() if k not in ('xaxis', 'yaxis')}
    fig_corr.update_layout(
        **corr_layout,
        xaxis=dict(title='Funding Percentile', gridcolor='rgba(0,0,0,0)', tickangle=-10),
        yaxis=dict(title='Avg Efficiency Score', gridcolor=BORDER),
    )

    # ── City ──────────────────────────────────────────────────────────────────
    city_top = city.nlargest(20, 'avg_efficiency').sort_values('avg_efficiency', ascending=False)
    fig_city = go.Figure(go.Bar(
        x=city_top['city'],
        y=city_top['avg_efficiency'],
        marker=dict(
            color=city_top['avg_efficiency'],
            colorscale=[[0, '#1E2D45'], [0.5, ACCENT2], [1, ACCENT]],
            line=dict(width=0)
        ),
        text=city_top['company_count'].apply(lambda x: f'{x}'),
        textposition='outside', textfont=dict(size=9, color=SUBTEXT),
        hovertemplate='<b>%{x}</b><br>Avg Score: %{y:.1f}<br>%{text} companies<extra></extra>'
    ))
    city_layout = {k: v for k, v in PLOT_LAYOUT.items() if k not in ('xaxis', 'yaxis')}
    fig_city.update_layout(
        **city_layout,
        xaxis=dict(tickangle=-35, gridcolor='rgba(0,0,0,0)'),
        yaxis=dict(title='Avg Efficiency Score', gridcolor=BORDER),
    )

    # ── Table ─────────────────────────────────────────────────────────────────
    table_df = df.sort_values('efficiency_score', ascending=False).head(100).copy()
    table_df['efficiency_score'] = table_df['efficiency_score'].round(1)
    table_df['total_funding'] = table_df['total_funding'].apply(
        lambda x: f'${x:,.0f}' if pd.notnull(x) else '—'
    )

    table = dash_table.DataTable(
        data=table_df.to_dict('records'),
        columns=[{'name': c.replace('_', ' ').title(), 'id': c} for c in table_df.columns],
        page_size=15, sort_action='native', filter_action='native',
        style_table={'overflowX': 'auto'},
        style_header={
            'backgroundColor': BG, 'color': ACCENT, 'fontFamily': FONT,
            'fontSize': '11px', 'letterSpacing': '1px',
            'border': f'1px solid {BORDER}', 'textTransform': 'uppercase',
        },
        style_cell={
            'backgroundColor': CARD_BG, 'color': TEXT, 'fontFamily': FONT,
            'fontSize': '12px', 'border': f'1px solid {BORDER}', 'padding': '10px 14px',
        },
        style_data_conditional=[
            {'if': {'filter_query': '{status} = acquired'}, 'color': STATUS_COLORS['acquired']},
            {'if': {'filter_query': '{status} = closed'},   'color': STATUS_COLORS['closed']},
            {'if': {'filter_query': '{status} = operating'},'color': STATUS_COLORS['operating']},
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#0D1526'},
        ],
    )

    return kpis, fig_leader, fig_ind, fig_stage, fig_corr, fig_city, table


if __name__ == '__main__':
    app.run(debug=True, port=8050)