"""
Executive dashboard style configuration - Power BI Style
Power BI palette, refined cards, edge-to-edge layout
"""

# ============================================================================
# SEMANTIC COLOR PALETTE (PREMIUM CONSULTING)
# ============================================================================
COLORS = {
    # Primary colors (executive)
    "primary": "#2E86AB",  # Executive blue
    "secondary": "#A23B72",  # Complementary purple
    "accent": "#F18F01",  # Highlight orange
    # Semantic colors
    "success": {
        "primary": "#28a745",  # Verde
        "light": "#d4edda",
        "dark": "#155724",
    },
    "warning": {
        "primary": "#ffc107",  # Amarelo
        "light": "#fff3cd",
        "dark": "#856404",
    },
    "danger": {
        "primary": "#dc3545",  # Vermelho
        "light": "#f8d7da",
        "dark": "#721c24",
    },
    "info": {
        "primary": "#17a2b8",  # Azul info
        "light": "#d1ecf1",
        "dark": "#0c5460",
    },
    "neutral": {
        "primary": "#6c757d",  # Cinza
        "light": "#f8f9fa",
        "dark": "#343a40",
    },
}

# ============================================================================
# TIPOGRAFIA
# ============================================================================
FONTS = {
    "primary": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    "monospace": "'Roboto Mono', 'Courier New', monospace",
    "sizes": {
        "h1": "2.5rem",  # 40px
        "h2": "2rem",  # 32px
        "h3": "1.5rem",  # 24px
        "h4": "1.25rem",  # 20px
        "h5": "1rem",  # 16px
        "h6": "0.875rem",  # 14px
        "body": "0.875rem",  # 14px
        "small": "0.75rem",  # 12px
        "kpi_hero": "4rem",  # 64px (KPI hero)
        "kpi_card": "2.5rem",  # 40px (cards regulares)
    },
    "weights": {
        "light": 300,
        "regular": 400,
        "medium": 500,
        "semibold": 600,
        "bold": 700,
    },
}

# ============================================================================
# ESTILOS COMPARTILHADOS
# ============================================================================
STYLES = {
    "border_radius": {
        "sm": "4px",
        "md": "8px",
        "lg": "12px",
        "xl": "16px",
        "circle": "50%",
    },
    "shadows": {
        "sm": "0 2px 4px rgba(0,0,0,0.05)",
        "md": "0 4px 8px rgba(0,0,0,0.08)",
        "lg": "0 8px 16px rgba(0,0,0,0.12)",
        "xl": "0 12px 24px rgba(0,0,0,0.15)",
        "inset": "inset 0 2px 4px rgba(0,0,0,0.05)",
    },
    "spacing": {
        "unit": "8px",
        "xs": "4px",
        "sm": "8px",
        "md": "16px",
        "lg": "24px",
        "xl": "32px",
        "xxl": "48px",
        "hero": "64px",
    },
    "transitions": {"fast": "150ms ease", "medium": "250ms ease", "slow": "350ms ease"},
}

# ============================================================================
# STYLE UTILITY FUNCTIONS
# ============================================================================


def get_kpi_color(kpi_name, value, category=None):
    """
    Determina status e cor apropriada baseado no valor do KPI

    Args:
        kpi_name: Nome do KPI
        value: Valor numérico
        category: Categoria do KPI (opcional)

    Returns:
        tuple: (status_text, color_hex)
    """
    # Safe conversion to float
    try:
        val_float = float(value) if value is not None else 0
    except (ValueError, TypeError):
        return "No Data", COLORS["neutral"]["primary"]

    # Specific logic per KPI type
    kpi_lower = str(kpi_name).lower()

    # 1. KPIs de SCORE (0-100)
    if "score" in kpi_lower or "index" in kpi_lower:
        if val_float >= 80:
            return "Excellent", COLORS["success"]["primary"]
        elif val_float >= 60:
            return "Good", "#ffc107"  # Amarelo custom
        elif val_float >= 40:
            return "Moderate", "#fd7e14"  # Laranja
        else:
            return "Needs Attention", COLORS["danger"]["primary"]

    # 2. GROWTH RATE KPIs (positive % is good)
    elif any(
        term in kpi_lower for term in ["growth", "increase", "rate", "yield", "return"]
    ):
        if val_float > 5:
            return "Strong Growth", COLORS["success"]["primary"]
        elif val_float > 0:
            return "Positive", "#ffc107"
        elif val_float == 0:
            return "Stable", COLORS["neutral"]["primary"]
        else:
            return "Declining", COLORS["danger"]["primary"]

    # 3. RISK/DEFICIT KPIs (lower is better)
    elif any(
        term in kpi_lower
        for term in ["deficit", "gap", "risk", "volatility", "uncertainty"]
    ):
        if val_float < 10:
            return "Low", COLORS["success"]["primary"]
        elif val_float < 25:
            return "Moderate", "#ffc107"
        else:
            return "High", COLORS["danger"]["primary"]

    # 4. KPIs de RATIO/PERCENT (0-100%)
    elif "%" in str(value) or any(
        term in kpi_lower for term in ["ratio", "penetration", "share"]
    ):
        if val_float < 10:
            return "Low", COLORS["success"]["primary"]
        elif val_float < 30:
            return "Moderate", "#ffc107"
        else:
            return "High", COLORS["danger"]["primary"]

    # 5. ABSOLUTE VALUE KPIs (context-specific)
    elif any(
        term in kpi_lower for term in ["price", "cost", "value", "housing", "rent"]
    ):
        # For monetary values, no status is applied by default
        return "Measured", COLORS["neutral"]["primary"]

    # 6. Fallback baseado em category
    elif category:
        if category in ["economic", "growth"]:
            return "Positive" if val_float > 0 else "Challenging", (
                COLORS["success"]["primary"]
                if val_float > 0
                else COLORS["danger"]["primary"]
            )
        elif category in ["risk", "volatility"]:
            color = (
                COLORS["danger"]["primary"]
                if val_float > 50
                else (
                    COLORS["warning"]["primary"]
                    if val_float > 25
                    else COLORS["success"]["primary"]
                )
            )
            status = (
                "High Risk"
                if val_float > 50
                else "Moderate Risk"
                if val_float > 25
                else "Low Risk"
            )
            return status, color

    # 7. Generic fallback based on value
    if val_float > 80:
        return "High", "#dc3545"
    elif val_float > 50:
        return "Moderate", "#ffc107"
    elif val_float > 20:
        return "Low", "#28a745"
    else:
        return "Very Low", COLORS["neutral"]["primary"]


def generate_gradient(color_hex, intensity="light"):
    """
    Gera gradiente baseado em uma cor

    Args:
        color_hex: Cor base (hex)
        intensity: 'light', 'medium' ou 'strong'

    Returns:
        str: String CSS para linear-gradient
    """
    intensities = {
        "light": ("15", "05"),
        "medium": ("30", "10"),
        "strong": ("50", "20"),
    }

    alpha_start, alpha_end = intensities.get(intensity, ("15", "05"))

    return f"""
        linear-gradient(
            135deg,
            {color_hex}{alpha_start} 0%,
            {color_hex}{alpha_end} 100%
        )
    """


def create_styled_header(title, level=2):
    """
    Create styled header

    Args:
        title: Texto do header
        level: Nível HTML (1-6)

    Returns:
        dict: Dict de estilo para Dash
    """
    tags = ["h1", "h2", "h3", "h4", "h5", "h6"]
    tag = tags[min(level - 1, 5)]

    return {
        "tag": tag,
        "children": title,
        "style": {
            "fontFamily": FONTS["primary"],
            "fontWeight": FONTS["weights"]["semibold"],
            "color": COLORS["neutral"]["dark"],
            "marginBottom": STYLES["spacing"]["md"],
        },
    }


def get_card_style(kpi_type="standard"):
    """
    Retorna estilo base para cards

    Args:
        kpi_type: 'standard', 'hero', 'info', 'warning', 'executive'

    Returns:
        dict: Dict de estilos
    """
    base_style = {
        "borderRadius": STYLES["border_radius"]["lg"],
        "boxShadow": STYLES["shadows"]["md"],
        "overflow": "hidden",
        "transition": f"all {STYLES['transitions']['medium']}",
    }

    type_styles = {
        "standard": {
            "border": f"1px solid {COLORS['neutral']['light']}",
            "backgroundColor": "white",
        },
        "hero": {
            "border": f"2px solid {COLORS['primary']}",
            "backgroundColor": generate_gradient(COLORS["primary"], "light"),
        },
        "info": {
            "border": f"1px solid {COLORS['info']['light']}",
            "backgroundColor": COLORS["info"]["light"],
        },
        "warning": {
            "border": f"1px solid {COLORS['warning']['light']}",
            "backgroundColor": COLORS["warning"]["light"],
        },
        "executive": {
            "border": "none",
            "borderRadius": "12px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
            "backgroundColor": "white",
        },
    }

    return {**base_style, **type_styles.get(kpi_type, type_styles["standard"])}


def get_affordability_color(value: float) -> str:
    """Retorna cor baseada no valor de affordability (menor é melhor)."""
    if value < 5:
        return "#28a745"  # verde
    elif value < 8:
        return "#ffc107"  # amarelo
    return "#dc3545"  # vermelho


def get_pressure_color(value: float) -> str:
    """Retorna cor baseada no valor de pressure (maior é pior)."""
    if value < 40:
        return "#28a745"  # verde
    elif value < 60:
        return "#ffc107"  # amarelo
    elif value < 80:
        return "#fd7e14"  # laranja
    return "#dc3545"  # vermelho
