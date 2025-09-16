import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import os

# --- Função manual para formatação de números no padrão brasileiro ---
def formatar_br(valor):
    """Formata um número para o padrão brasileiro (ex: 12.000,00)."""
    try:
        s = f"{valor:,.2f}"
        s = s.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        return s
    except (ValueError, TypeError):
        return str(valor)

st.set_page_config(page_title="Vulnerabilidade Econômica - Rio Grande", layout="wide")

# --- CSS DEFINITIVO para ajustar layout ---
st.markdown("""
    <style>
    /* Ajustes gerais de espaçamento */
    div.block-container { padding-top: 1.5rem; }
    h1 { padding-bottom: 0.5rem; }

    /* --- CSS PARA AGRUPAR AS MÉTRICAS --- */
    [data-testid="stHorizontalBlock"] { gap: 0.75rem; }
    [data-testid="stMetric"] { background-color: #FAFAFA; border: 1px solid #EEEEEE; padding: 1rem; border-radius: 0.5rem; }
    
    /* --- Estilos da Sidebar --- */
    .sidebar-logo-bottom { position: absolute; bottom: 1rem; left: 0; right: 0; text-align: center; }
    .sidebar-logo-bottom img { max-width: 70%; height: auto; display: block; margin: auto; }
    
    /* ALTERAÇÃO: Espaçamento do rodapé reduzido */
    hr {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🌊 Vulnerabilidade Econômica a Desastres Hidrológicos em Rio Grande")

# --- Funções de Carregamento de Dados ---
@st.cache_data
def carregar_shapefile(caminho_completo):
    gdf = gpd.read_file(caminho_completo, encoding='utf-8')
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326", allow_override=True)
    return gdf

@st.cache_data
def carregar_empresas_xlsx(caminho_completo):
    try:
        df = pd.read_excel(caminho_completo)
        df.dropna(subset=['latitude', 'longitude'], inplace=True)
        return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326")
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo de empresas: {e}")
        return None

# --- Carregamento de Todos os Dados ---
with st.spinner('Carregando dados geoespaciais...'):
    pasta_dados = "Dados"
    gpea_logo_path = "GPEA.png"
    ciex_logo_path = "CIEX.png" 
    bairros_gdf = carregar_shapefile(os.path.join(pasta_dados, 'PMRG_231215_layer_Bairros.shp'))
    logradouros_gdf = carregar_shapefile(os.path.join(pasta_dados, 'PMRG_231215_layer_Logradouros_segmentos.shp'))
    mancha_mai2024_gdf = carregar_shapefile(os.path.join(pasta_dados, 'CEN_MAI2024.shp'))
    mancha_set2023_gdf = carregar_shapefile(os.path.join(pasta_dados, 'CEN_SET2023.shp'))
    quadras_gdf = carregar_shapefile(os.path.join(pasta_dados, 'PMRG_231215_layer_Quadras.shp'))
    terrenos_gdf = carregar_shapefile(os.path.join(pasta_dados, 'PMRG_231215_layer_Terrenos.shp'))
    empresas_gdf = carregar_empresas_xlsx(os.path.join(pasta_dados, 'RAIS e Receita (Georrefenciada).xlsx'))

# --- Barra Lateral (Sidebar) ---
st.sidebar.image(gpea_logo_path, use_container_width=True)
st.sidebar.header("Controle de Camadas")
# ... (código da sidebar continua igual)
mostrar_bairros = st.sidebar.checkbox("Bairros", value=True)
mostrar_quadras = st.sidebar.checkbox("Quadras", value=True)
mostrar_logradouros = st.sidebar.checkbox("Logradouros (Ruas)", value=False)
mostrar_terrenos = st.sidebar.checkbox("Terrenos", value=False)
mostrar_empresas = st.sidebar.checkbox("Empresas", value=True)
st.sidebar.markdown("### Cenários de Inundação")
opcoes_manchas = {"Nenhum": None, "Maio de 2024": mancha_mai2024_gdf, "Setembro de 2023": mancha_set2023_gdf}
lista_opcoes = list(opcoes_manchas.keys())
indice_padrao = lista_opcoes.index("Maio de 2024")
selecao_mancha_nome = st.sidebar.selectbox("Selecione o Cenário:", options=lista_opcoes, index=indice_padrao)
mancha_selecionada_gdf = opcoes_manchas[selecao_mancha_nome]
mostrar_apenas_atingidos = st.sidebar.checkbox("Mostrar Apenas Atingidos")

# --- Lógica de Análise e Filtros ---
if mostrar_apenas_atingidos and mancha_selecionada_gdf is not None and empresas_gdf is not None:
    empresas_4326 = empresas_gdf.to_crs("EPSG:4326")
    mancha_4326 = mancha_selecionada_gdf.to_crs("EPSG:4326")
    base_empresas_gdf = gpd.sjoin(empresas_4326, mancha_4326, how="inner", predicate="within")
else:
    base_empresas_gdf = empresas_gdf

empresas_filtradas = base_empresas_gdf
if mostrar_empresas and base_empresas_gdf is not None:
    st.sidebar.markdown("### Filtros de Empresas")
    # ... (código dos filtros da sidebar continua igual)
    setores_opcoes, subsetores_opcoes, situacoes_opcoes = sorted(base_empresas_gdf['Seção'].dropna().unique()), sorted(base_empresas_gdf['Denominação'].dropna().unique()), sorted(base_empresas_gdf['situacao_cadastral_desc'].dropna().unique())
    setor_selecionado = st.sidebar.multiselect("Setor", options=setores_opcoes, default=[])
    subsetor_selecionado = st.sidebar.multiselect("Subsetor", options=subsetores_opcoes, default=[])
    default_situacao = ['ATIVA'] if 'ATIVA' in situacoes_opcoes else []
    situacao_selecionada = st.sidebar.multiselect("Situação Cadastral", options=situacoes_opcoes, default=default_situacao)
    if setor_selecionado:
        empresas_filtradas = empresas_filtradas[empresas_filtradas['Seção'].isin(setor_selecionado)]
    if subsetor_selecionado:
        empresas_filtradas = empresas_filtradas[empresas_filtradas['Denominação'].isin(subsetor_selecionado)]
    if situacao_selecionada:
        empresas_filtradas = empresas_filtradas[empresas_filtradas['situacao_cadastral_desc'].isin(situacao_selecionada)]

st.sidebar.markdown('<div class="sidebar-logo-bottom">', unsafe_allow_html=True)
if os.path.exists(ciex_logo_path):
    st.sidebar.image(ciex_logo_path, use_container_width=True)
st.sidebar.markdown('</div>', unsafe_allow_html=True)
empresas_para_plotar = empresas_filtradas

# --- Exibição de Métricas ---
if mostrar_apenas_atingidos and mancha_selecionada_gdf is not None and empresas_gdf is not None:
    atingidos_gdf = base_empresas_gdf
    st.subheader(f"Impacto Comparativo para o Cenário: {selecao_mancha_nome}")
    # ... (código das métricas igual)
    col1, col2, col3, col4 = st.columns(4)
    total_empresas, total_empregados, total_massa_salarial, media_salarial_geral = len(empresas_gdf), empresas_gdf['Empregados'].sum(), empresas_gdf['Massa_Salarial'].sum(), empresas_gdf['MédiaSalarial'].mean()
    if not atingidos_gdf.empty:
        total_empresas_atingidas, total_empregados_atingidos, total_massa_salarial_atingida, media_salarial_atingida = len(atingidos_gdf), atingidos_gdf['Empregados'].sum(), atingidos_gdf['Massa_Salarial'].sum(), atingidos_gdf['MédiaSalarial'].mean()
    else:
        total_empresas_atingidas, total_empregados_atingidos, total_massa_salarial_atingida, media_salarial_atingida = 0, 0, 0, 0
    perc_empresas, perc_empregados, perc_massa_salarial = ((total_empresas_atingidas / total_empresas * 100) if total_empresas > 0 else 0, (total_empregados_atingidos / total_empregados * 100) if total_empregados > 0 else 0, (total_massa_salarial_atingida / total_massa_salarial * 100) if total_massa_salarial > 0 else 0)
    delta_empresas = f"de {total_empresas} no Total ({perc_empresas:,.1f}%)".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    col1.metric(label="Empresas Atingidas", value=f"{total_empresas_atingidas}", delta=delta_empresas, delta_color="off")
    empregados_atingidos_fmt, empregados_total_fmt = f"{int(total_empregados_atingidos):,}".replace(",", "."), f"{int(total_empregados):,}".replace(",", ".")
    delta_empregados = f"de {empregados_total_fmt} no Total ({perc_empregados:,.1f}%)".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    col2.metric(label="Empregados Atingidos", value=empregados_atingidos_fmt, delta=delta_empregados, delta_color="off")
    massa_atingida_fmt, delta_massa = f"R$ {formatar_br(total_massa_salarial_atingida)}", f"de {formatar_br(total_massa_salarial)} no Total ({perc_massa_salarial:,.1f}%)".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    col3.metric(label="Massa Salarial Atingida", value=massa_atingida_fmt, delta=delta_massa, delta_color="off")
    media_atingida_fmt, media_geral_fmt = f"R$ {formatar_br(media_salarial_atingida)}", f"de {formatar_br(media_salarial_geral)} no Total"
    col4.metric(label="Média Salarial (Atingidos)", value=media_atingida_fmt, delta=media_geral_fmt, delta_color="off")
elif mostrar_empresas and empresas_gdf is not None:
    st.subheader("Visão Geral")
    col1, col2, col3, col4 = st.columns(4)
    total_empresas, total_empregados, total_massa_salarial, media_salarial_geral = len(empresas_gdf), empresas_gdf['Empregados'].sum(), empresas_gdf['Massa_Salarial'].sum(), empresas_gdf['MédiaSalarial'].mean()
    massa_total_formatada, media_total_formatada = f"R$ {formatar_br(total_massa_salarial)}", f"R$ {formatar_br(media_salarial_geral)}"
    col1.metric("Total de Empresas", f"{total_empresas}")
    col2.metric("Total de Empregados", f"{int(total_empregados):,}".replace(",", "."))
    col3.metric("Massa Salarial Total", massa_total_formatada)
    col4.metric("Média Salarial Geral", media_total_formatada)

# --- Criação do Mapa ---
st.subheader("Mapa Interativo")
# CORREÇÃO: Usa a sintaxe correta 'with st.spinner(...)'
with st.spinner("Atualizando mapa..."):
    m = folium.Map(location=[-32.0353, -52.0986], zoom_start=13, tiles="CartoDB positron")
    if mancha_selecionada_gdf is not None:
        folium.GeoJson(mancha_selecionada_gdf, name=selecao_mancha_nome, show=True, tooltip=selecao_mancha_nome, style_function=lambda x: {'color': 'blue', 'weight': 1.5, 'fillColor': '#3186cc', 'fillOpacity': 0.6}).add_to(m)
    if bairros_gdf is not None:
        folium.GeoJson(bairros_gdf, name="Bairros", show=mostrar_bairros, tooltip=folium.features.GeoJsonTooltip(fields=['nm_bairro'], aliases=['Bairro:']), style_function=lambda x: {'color': 'black', 'weight': 2, 'fillOpacity': 0}).add_to(m)
    if quadras_gdf is not None:
        folium.GeoJson(quadras_gdf, name="Quadras", show=mostrar_quadras, tooltip=folium.features.GeoJsonTooltip(fields=['numero', 'area'], aliases=['Nº da Quadra:', 'Área (m²):']), style_function=lambda x: {'color': '#444444', 'weight': 1, 'fillColor': 'grey', 'fillOpacity': 0.2}).add_to(m)
    if logradouros_gdf is not None:
        folium.GeoJson(logradouros_gdf, name="Logradouros", show=mostrar_logradouros, tooltip=folium.features.GeoJsonTooltip(fields=['tipo', 'nome'], aliases=['Tipo:', 'Nome:']), style_function=lambda x: {'color': 'dodgerblue', 'weight': 2.5}).add_to(m)
    if terrenos_gdf is not None:
        folium.GeoJson(terrenos_gdf, name="Terrenos", show=mostrar_terrenos, tooltip=folium.features.GeoJsonTooltip(fields=['area_lote'], aliases=['Área do Lote (m²):']), style_function=lambda x: {'color': '#966919', 'weight': 0.5, 'fillColor': '#966919', 'fillOpacity': 0.3}).add_to(m)
    if mostrar_empresas and empresas_para_plotar is not None and not empresas_para_plotar.empty:
        mc = MarkerCluster(name="Empresas").add_to(m)
        for idx, row in empresas_para_plotar.iterrows():
            massa_salarial_pop = formatar_br(row.get('Massa_Salarial', 0))
            media_salarial_pop = formatar_br(row.get('MédiaSalarial', 0))
            popup_html = f"<b>ID:</b> {row.get('id', 'N/A')}<br><b>Empregados:</b> {row.get('Empregados', 'N/A')}<br><b>Massa Salarial:</b> R$ {massa_salarial_pop}<br><b>Média Salarial:</b> R$ {media_salarial_pop}"
            folium.Marker(location=[row.latitude, row.longitude], popup=folium.Popup(popup_html, max_width=300)).add_to(mc)
    folium.LayerControl().add_to(m)
    st_folium(m, width="100%", height=700, returned_objects=[])

# --- Rodapé ---
st.markdown("---")
st.markdown(f"© {2025} Grupo de Pesquisa em Economia Aplicada, Universidade Federal de Rio Grande - FURG. Todos os direitos reservados.")
footer_html = """
<style>
.footer {
    position: fixed;
    bottom: 8px;
    right: 8px;
    font-size: 8pt;
    color: #777777;
    text-align: right;
}
</style>
<div class="footer">
    Desenvolvido por Alisson Tallys Geraldo Fiorentin
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)