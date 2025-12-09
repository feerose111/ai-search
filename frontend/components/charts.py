import pandas as pd
from backend.utils.feature.history import get_history
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re


def load_query_data():
    try:
        history = get_history()
        if not history:
            return pd.DataFrame()

        df = pd.DataFrame(history)

        # Ensure correct datetime conversion
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        return df
    except Exception as e:
        print(f"❌ Failed to load query data from Redis: {e}")
        return pd.DataFrame()


def chart_intent_frequency(df):
    intents = df["parsed_query"].apply(lambda q: q.get("intent"))
    intent_counts = Counter(intents)
    df_intents = pd.DataFrame(intent_counts.items(), columns=["intent", "count"])

    # Modern color palette with vibrant colors
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#FFB6C1', '#98FB98']

    fig = px.pie(df_intents, names="intent", values="count",
                 title="Query Intent Distribution",
                 color_discrete_sequence=colors)

    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        textfont_size=12,
        marker=dict(line=dict(color='#FFFFFF', width=2)),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )
    fig.update_layout(
        showlegend=True,
        font=dict(size=12, family="Inter, sans-serif"),
        title_x=0.5,
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig


def chart_word_frequency(df):
    stopwords = {"the", "and", "or", "give", "me", "is", "to", "of", "between", "for", "on", "in", "at", "with", "a"}
    queries = df["raw_query"]
    words = []
    for q in queries:
        q = re.sub(r"[^\w\s]", "", q.lower())
        words.extend([word for word in q.split() if word not in stopwords])
    word_counts = Counter(words).most_common(20)
    df_words = pd.DataFrame(word_counts, columns=["word", "count"])

    # Gradient color scale from orange to blue
    fig = go.Figure(data=[
        go.Bar(
            x=df_words["count"],
            y=df_words["word"],
            orientation='h',
            marker=dict(
                color=df_words["count"],
                colorscale='Viridis',
                showscale=False,
                line=dict(color='rgba(255,255,255,0.8)', width=1)
            ),
            text=df_words["count"],
            textposition='outside',
            textfont=dict(color='white', size=11),
            hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>'
        )
    ])

    fig.update_layout(
        title="Top 20 Most Frequent Keywords",
        title_x=0.5,
        height=500,
        xaxis_title="Frequency",
        yaxis_title="Keywords",
        yaxis={'categoryorder': 'total ascending'},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif"),
        margin=dict(l=100, r=50, t=60, b=50)
    )
    return fig


def chart_query_volume(df):
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date
    daily = df.groupby("date").size().reset_index(name="query_count")

    # Create area chart with gradient fill
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=daily["date"],
        y=daily["query_count"],
        mode='lines+markers',
        fill='tonexty',
        fillcolor='rgba(255, 107, 53, 0.3)',
        line=dict(color='#FF6B35', width=3),
        marker=dict(
            size=8,
            color='#FF6B35',
            line=dict(width=2, color='white')
        ),
        name='Daily Queries',
        hovertemplate='Date: %{x}<br>Queries: %{y}<extra></extra>'
    ))

    fig.update_layout(
        title="Daily Query Volume Trend",
        title_x=0.5,
        height=400,
        xaxis_title="Date",
        yaxis_title="Number of Queries",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif"),
        hovermode='x unified',
        showlegend=False
    )
    return fig


def chart_query_heatmap(df):
    """Create a heatmap showing query patterns by time and intent"""
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["timestamp"].dt.hour
    df["intent"] = df["parsed_query"].apply(lambda q: q.get("intent", "unknown"))

    # Create pivot table for heatmap
    heatmap_data = df.groupby(['hour', 'intent']).size().reset_index(name='count')
    pivot_data = heatmap_data.pivot(index='intent', columns='hour', values='count').fillna(0)

    # Create heatmap with custom colorscale
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='RdYlBu_r',
        showscale=True,
        colorbar=dict(title="Query Count"),
        hovertemplate='Hour: %{x}<br>Intent: %{y}<br>Queries: %{z}<extra></extra>'
    ))

    fig.update_layout(
        title="Query Heatmap (Time vs Intent)",
        title_x=0.5,
        height=400,
        xaxis_title="Hour of Day",
        yaxis_title="Query Intent",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif")
    )
    return fig