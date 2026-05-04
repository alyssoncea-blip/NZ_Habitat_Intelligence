"""
Components de charts para dashboard premium
Wrapper para Plotly com estilos executives
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from ..utils.style_config import COLORS

def create_line_chart(df, x_col, y_col, title="", color=None, show_range=True):
    """
    Create premium line chart
    
    Args:
        df: DataFrame com data
        x_col: Coluna para eixo X
        y_col: Coluna para eixo Y
        title: Título do gráfico
        color: Color da linha (hex)
        show_range: Se True, mostra área de range
    
    Returns:
        go.Figure configurada
    """
    color = color or COLORS['primary']
    
    fig = go.Figure()
    
    # Linha principal
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode='lines',
        name=y_col,
        line=dict(color=color, width=3),
        hovertemplate='<b>%{x}</b><br>%{y:.1f}<extra></extra>'
    ))
    
    # Range area (optional)
    if show_range and len(df) > 1:
        y_rolling = df[y_col].rolling(window=3, center=True, min_periods=1).mean()
        y_std = df[y_col].rolling(window=3, center=True, min_periods=1).std().fillna(0)
        
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=y_rolling + y_std,
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=y_rolling - y_std,
            mode='lines',
            fill='tonexty',
            fillcolor=f'{color}20',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Estilo premium
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color=COLORS['neutral']['dark']),
            x=0.5
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        margin=dict(l=60, r=30, t=50, b=50),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            tickfont=dict(size=12)
        ),
        showlegend=False
    )
    
    return fig

def create_gauge_chart(value, title="", min_val=0, max_val=100, color=None):
    """
    Create premium gauge chart (circular indicator)
    
    Args:
        value: Valor atual
        title: Título do gauge
        min_val: Valor mínimo
        max_val: Valor máximo
        color: Color do gauge (auto por padrão)
    
    Returns:
        go.Figure configurada
    """
    # Determina color baseado no valor
    if not color:
        percentage = (value - min_val) / (max_val - min_val) * 100
        if percentage >= 80:
            color = COLORS['success']['primary']
        elif percentage >= 60:
            color = '#ffc107'
        elif percentage >= 40:
            color = '#fd7e14'
        else:
            color = COLORS['danger']['primary']
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 16}},
        number={'font': {'size': 40, 'color': color}},
        gauge={
            'axis': {'range': [min_val, max_val], 'tickwidth': 1, 'tickcolor': COLORS['neutral']['dark']},
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': COLORS['neutral']['light'],
            'steps': [
                {'range': [min_val, max_val*0.6], 'color': '#f0f0f0'},
                {'range': [max_val*0.6, max_val*0.8], 'color': '#f8f8f8'},
                {'range': [max_val*0.8, max_val], 'color': '#ffffff'}
            ],
            'threshold': {
                'line': {'color': color, 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='white',
        margin=dict(l=30, r=30, t=50, b=30),
        height=300
    )
    
    return fig

def create_bar_chart(df, x_col, y_col, title="", color_scale=None, horizontal=False):
    """
    Create premium bar chart
    
    Args:
        df: DataFrame com data
        x_col: Column for X axis (or categories)
        y_col: Coluna para eixo Y (valores)
        title: Título do gráfico
        color_scale: Escala de colores (opcional)
        horizontal: Se True, barras horizontais
    
    Returns:
        go.Figure configurada
    """
    if not color_scale:
        color_scale = [COLORS['info']['primary'], COLORS['primary']]
    
    if horizontal:
        orientation = 'h'
        x = df[y_col]
        y = df[x_col]
    else:
        orientation = 'v'
        x = df[x_col]
        y = df[y_col]
    
    fig = go.Figure(data=go.Bar(
        x=x,
        y=y,
        orientation=orientation,
        marker=dict(
            color=y,
            colorscale=color_scale,
            showscale=False,
            line=dict(color='white', width=1)
        ),
        hovertemplate='<b>%{y if horizontal else "%{x}"}</b><br>%{x if horizontal else "%{y}"}<extra></extra>',
        text=y.round(1) if y.dtype.kind in 'ifc' else y,
        textposition='outside'
    ))
    
    title_config = dict(
        text=title,
        font=dict(size=16, color=COLORS['neutral']['dark']),
        x=0.5
    )
    
    fig.update_layout(
        title=title_config,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=30, t=50, b=50),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            tickfont=dict(size=12)
        ),
        showlegend=False
    )
    
    if horizontal:
        fig.update_yaxes(autorange="reversed")
    
    return fig

def create_scatter_plot(df, x_col, y_col, color_col=None, title="", size_col=None):
    """
    Create premium scatter plot
    
    Args:
        df: DataFrame com data
        x_col: Coluna para eixo X
        y_col: Coluna para eixo Y
        color_col: Coluna para colores (opcional)
        title: Título do gráfico
        size_col: Coluna para tamanhos (opcional)
    
    Returns:
        go.Figure configurada
    """
    fig = px.scatter(
        df, 
        x=x_col, 
        y=y_col,
        color=color_col,
        size=size_col,
        title=title,
        color_continuous_scale=[COLORS['info']['primary'], COLORS['primary']]
    )
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=30, t=50, b=50),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            tickfont=dict(size=12)
        )
    )
    
    return fig

def create_heatmap(matrix_df, title="", color_scale=None):
    """
    Create premium heatmap
    
    Args:
        matrix_df: DataFrame com matriz de valores
        title: Título do heatmap
        color_scale: Escala de colores (opcional)
    
    Returns:
        go.Figure configurada
    """
    if not color_scale:
        color_scale = [[0, COLORS['info']['light']], [1, COLORS['primary']]]
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix_df.values,
        x=matrix_df.columns,
        y=matrix_df.index,
        colorscale=color_scale,
        hovertemplate='<b>%{y} × %{x}</b><br>Value: %{z:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color=COLORS['neutral']['dark']),
            x=0.5
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=80, r=30, t=50, b=80),
        xaxis=dict(
            tickangle=45,
            tickfont=dict(size=11)
        ),
        yaxis=dict(
            tickfont=dict(size=11)
        )
    )
    
    return fig

def create_multi_chart(df, x_col, y_cols, title="", chart_types=None):
    """
    Create multi-series chart
    
    Args:
        df: DataFrame com data
        x_col: Coluna para eixo X
        y_cols: Lista de colunas para eixo Y
        title: Título do gráfico
        chart_types: Lista de tipos ('line', 'bar') para cada série
    
    Returns:
        go.Figure configurada
    """
    if not chart_types:
        chart_types = ['line'] * len(y_cols)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    colors = [COLORS['primary'], COLORS['secondary'], COLORS['accent'], 
              COLORS['success']['primary'], COLORS['warning']['primary']]
    
    for i, (y_col, chart_type) in enumerate(zip(y_cols, chart_types)):
        color = colors[i % len(colors)]
        
        if chart_type == 'line':
            fig.add_trace(
                go.Scatter(
                    x=df[x_col],
                    y=df[y_col],
                    name=y_col,
                    line=dict(color=color, width=2 if i == 0 else 1.5),
                    mode='lines',
                    hovertemplate=f'<b>{y_col}</b><br>%{{x}}<br>%{{y:.1f}}<extra></extra>'
                ),
                secondary_y=(i > 0)  # First series on main Y axis
            )
        elif chart_type == 'bar':
            fig.add_trace(
                go.Bar(
                    x=df[x_col],
                    y=df[y_col],
                    name=y_col,
                    marker_color=color,
                    opacity=0.7,
                    hovertemplate=f'<b>{y_col}</b><br>%{{x}}<br>%{{y:.1f}}<extra></extra>'
                ),
                secondary_y=(i > 0)
            )
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        margin=dict(l=60, r=60, t=50, b=50),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(255,255,255,0.9)'
        )
    )
    
    fig.update_xaxes(title_text=x_col, showgrid=True, gridcolor='rgba(0,0,0,0.05)')
    fig.update_yaxes(title_text=y_cols[0], secondary_y=False, showgrid=True, gridcolor='rgba(0,0,0,0.05)')
    
    if len(y_cols) > 1:
        fig.update_yaxes(title_text=y_cols[1], secondary_y=True, showgrid=False)
    
    return fig
