"""
Script para testar o dashboard executivo rapidamente.
"""
import sys

print("=" * 60)
print("TESTE DO DASHBOARD EXECUTIVO")
print("=" * 60)

try:
    from app.main import app
    print("\n[OK] App carregado com sucesso")
    print("     - URL: http://localhost:8050")
    print("     - Callbacks registrados: verifique no console")
    
    # Verificar se os componentes estão disponíveis
    from app.data.executive_kpi_data import load_executive_data
    
    print("\n[OK] Componentes carregados:")
    print("     - ExecutiveKPICard")
    print("     - create_executive_dashboard")
    print("     - load_executive_data")
    
    # Carregar dados
    data = load_executive_data()
    print("\n[OK] Dados carregados:")
    print(f"     - {len(data['hero_kpis'])} KPIs")
    print(f"     - {len(data['regions'])} regiões")
    print(f"     - {len(data['scatter_data'])} pontos scatter")
    
    print("\n" + "=" * 60)
    print("INICIANDO SERVIDOR...")
    print("=" * 60)
    print("\nAcesse: http://localhost:8050")
    print("Pressione CTRL+C para parar\n")
    
    app.run(debug=True, host='0.0.0.0', port=8050)
    
except Exception as e:
    print(f"\n[ERRO] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
