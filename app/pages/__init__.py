"""
Páginas do dashboard
Cada arquivo representa um dashboard específico
"""
from .executive import create_executive_dashboard
from .housing import create_housing_dashboard
from .tourism import create_tourism_dashboard
from .macro import create_macro_dashboard
from .affordability import create_affordability_dashboard
from .forecast import create_forecast_dashboard

__all__ = [
    'create_executive_dashboard',
    'create_housing_dashboard',
    'create_tourism_dashboard', 
    'create_macro_dashboard',
    'create_affordability_dashboard',
    'create_forecast_dashboard'
]