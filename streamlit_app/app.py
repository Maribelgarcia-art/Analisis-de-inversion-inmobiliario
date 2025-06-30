import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import traceback

st.set_page_config(
    page_title="Panel de Análisis de mercado inmobiliario (AirBnb)",
    page_icon="🏠📊",
    layout="wide"
)

st.title("🏠📊 Panel de Análisis de mercado inmobiliario (AirBnb)")
st.markdown("""
Este panel te permite explorar datos del mercado inmobiliario en Valencia, Málaga, Madrid y Barcelona para su inversión.
Utiliza los filtros y selectores en la barra lateral para personalizar tu análisis.
""")

@st.cache_data(ttl=3600)
def load_data():
    try:
        df = pd.read_csv('data/Valencia_limpio.csv')
        df_inmobiliario = pd.read_csv("data/valencia_vivienda_limpio.csv")
        df_delincuencia = pd.read_csv("data/crimenValencia.csv", sep=';')
        return df, df_inmobiliario, df_delincuencia
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        st.text(traceback.format_exc())
        return None, None, None

df, df_inmobiliario, df_delincuencia = load_data()

# Preprocesamiento básico y filtros
if df is not None and df_inmobiliario is not None:
    if 'price' in df.columns:
        df['price'] = df['price'].astype(float)
    if 'precio' in df_inmobiliario.columns:
        precio_m2_valencia = df_inmobiliario['precio'].mean()
    else:
        precio_m2_valencia = 2000  # fallback
    average_m2 = 70
    df['annual_income'] = df['price'] * df['days_rented']
    df['estimated_property_value'] = precio_m2_valencia * average_m2
    df['ROI (%)'] = (df['annual_income'] / df['estimated_property_value']) * 100
    gastos_anuales = 3000
    df['net_annual_income'] = df['annual_income'] - gastos_anuales
    df['Net ROI (%)'] = (df['net_annual_income'] / df['estimated_property_value']) * 100

    st.sidebar.header("Filtros")

    # Filtro por ciudad
    ciudades = ['Valencia', 'Malaga', 'Madrid', 'Barcelona']
    if 'city' in df.columns:
        ciudad_seleccionada = st.sidebar.selectbox("Selecciona ciudad", ciudades)
        df_ciudad = df[df['city'].str.lower() == ciudad_seleccionada.lower()]
        if df_ciudad.empty:
            st.warning("No hay datos para la ciudad seleccionada.")
            st.stop()
        barrios = sorted(df_ciudad['neighbourhood'].dropna().unique())
        selected_barrios = st.sidebar.multiselect("Selecciona barrios", options=barrios, default=barrios)
        df_ciudad = df_ciudad[df_ciudad['neighbourhood'].isin(selected_barrios)]
        if df_ciudad.empty:
            st.warning("No hay datos para los barrios seleccionados en la ciudad.")
            st.stop()
        df = df_ciudad
    else:
        st.sidebar.warning("No se encontró la columna 'city' en los datos. Mostrando todos los datos.")
        barrios = sorted(df['neighbourhood'].dropna().unique())
        selected_barrios = st.sidebar.multiselect("Selecciona barrios", options=barrios, default=barrios)
        df = df[df['neighbourhood'].isin(selected_barrios)]
        if df.empty:
            st.warning("No hay datos para los barrios seleccionados.")
            st.stop()
else:
    st.warning("No hay datos disponibles.")
    st.stop()

main_tabs = st.tabs([
    "📊 Resumen General",
    "🏠 Precios de Vivienda",
    "💸 Rentabilidad por Barrio",
    "📈 Competencia y Demanda",
    "🔍 Análisis Avanzado",
    "📝 Conclusiones"
])

# ------------------ Pestaña 1: Resumen General ------------------
with main_tabs[0]:
    st.subheader("Resumen General del Mercado Inmobiliario")
    col1, col2, col3 = st.columns(3)
    col1.metric("Nº de anuncios", len(df))
    col2.metric("ROI Neto medio (%)", f"{df['Net ROI (%)'].mean():.2f}")
    col3.metric("Precio medio alquiler (€)", f"{df['price'].mean():.2f}")

    # KDE ROI Bruto y Neto
    st.markdown("#### Distribución de ROI Bruto y Neto (%)")
    if len(df) > 1:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.kdeplot(df['ROI (%)'], fill=True, label='ROI Bruto (%)', color='skyblue', bw_adjust=0.7, clip=(0, 50), ax=ax)
        sns.kdeplot(df['Net ROI (%)'], fill=True, label='ROI Neto (%)', color='orange', bw_adjust=0.7, clip=(0, 50), ax=ax)
        ax.set_title('Distribución de ROI Bruto y Neto')
        ax.set_xlabel('ROI (%)')
        ax.set_ylabel('Densidad')
        ax.set_xlim(0, 50)
        ax.legend()
        st.pyplot(fig)
    else:
        st.info("No hay suficientes datos para mostrar la distribución de ROI.")

# ------------------ Pestaña 2: Precios de Vivienda ------------------
with main_tabs[1]:
    st.subheader("Precios de Vivienda por Barrio")
    if 'precio' in df_inmobiliario.columns:
        barrio_caros = df_inmobiliario.groupby('neighbourhood')['precio'].mean().reset_index()
        barrio_caros = barrio_caros.sort_values(by='precio', ascending=False).head(15)
        if not barrio_caros.empty:
            fig_precio = px.bar(
                barrio_caros,
                x='precio',
                y='neighbourhood',
                orientation='h',
                labels={'precio': 'Precio medio m2 de compra (€)', 'neighbourhood': 'Barrio'},
                title='Top 15 barrios más caros por precio medio m2 de compra'
            )
            st.plotly_chart(fig_precio, use_container_width=True)
        else:
            st.info("No hay datos de precios de vivienda para mostrar.")
    else:
        st.info("No hay datos de precios de vivienda para mostrar.")

# ------------------ Pestaña 3: Rentabilidad por Barrio ------------------
with main_tabs[2]:
    st.subheader("Rentabilidad por Barrio")
    if not df.empty:
        # ROI neto por barrio
        roi_barrio = df.groupby('neighbourhood')['Net ROI (%)'].mean().sort_values(ascending=False).head(15)
        if not roi_barrio.empty:
            fig_roi = px.bar(
                roi_barrio,
                x=roi_barrio.values,
                y=roi_barrio.index,
                orientation='h',
                labels={'x': 'ROI Neto (%)', 'y': 'Barrio'},
                title='Top 15 barrios por ROI Neto (%)'
            )
            st.plotly_chart(fig_roi, use_container_width=True)
        else:
            st.info("No hay datos de ROI Neto para mostrar.")

        # ROI bruto por barrio
        roi_barrio_bruto = df.groupby('neighbourhood')['ROI (%)'].mean().sort_values(ascending=False).head(15)
        if not roi_barrio_bruto.empty:
            fig_roi_bruto = px.bar(
                roi_barrio_bruto,
                x=roi_barrio_bruto.values,
                y=roi_barrio_bruto.index,
                orientation='h',
                labels={'x': 'ROI Bruto (%)', 'y': 'Barrio'},
                title='Top 15 barrios por ROI Bruto (%)'
            )
            st.plotly_chart(fig_roi_bruto, use_container_width=True)
        else:
            st.info("No hay datos de ROI Bruto para mostrar.")
    else:
        st.info("No hay datos para mostrar en esta pestaña.")

# ------------------ Pestaña 4: Competencia y Demanda ------------------
with main_tabs[3]:
    st.subheader("Competencia y Demanda por Barrio")
    if not df.empty:
        # Competencia por barrio
        competencia_por_barrio = df.groupby('neighbourhood')['id'].count().reset_index().rename(columns={'id': 'n_anuncios'})
        top_comp = competencia_por_barrio.sort_values(by='n_anuncios', ascending=False).head(15)
        if not top_comp.empty:
            fig_comp = px.bar(
                top_comp,
                x='n_anuncios',
                y='neighbourhood',
                orientation='h',
                labels={'n_anuncios': 'Nº de anuncios', 'neighbourhood': 'Barrio'},
                title='Top 15 barrios con más competencia (nº de anuncios)'
            )
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("No hay datos de competencia para mostrar.")

        # Anuncios activos (>30 días alquilados/año)
        if 'days_rented' in df.columns:
            activos = df[df['days_rented'] > 30]
            competencia_activa = activos.groupby('neighbourhood')['id'].count().reset_index().rename(columns={'id': 'n_anuncios_activos'})
            top_activos = competencia_activa.sort_values(by='n_anuncios_activos', ascending=False).head(15)
            if not top_activos.empty:
                fig_activos = px.bar(
                    top_activos,
                    x='n_anuncios_activos',
                    y='neighbourhood',
                    orientation='h',
                    labels={'n_anuncios_activos': 'Nº de anuncios activos', 'neighbourhood': 'Barrio'},
                    title='Top 15 barrios con más anuncios activos (>30 días alquilados/año)'
                )
                st.plotly_chart(fig_activos, use_container_width=True)
            else:
                st.info("No hay datos de anuncios activos para mostrar.")
        else:
            st.info("No hay datos de días alquilados para mostrar anuncios activos.")
    else:
        st.info("No hay datos para mostrar en esta pestaña.")

# ------------------ Pestaña 5: Análisis Avanzado ------------------
with main_tabs[4]:
    st.subheader("Análisis Avanzado")
    if not df.empty:
        # Relación entre precio medio de alquiler y ROI neto por barrio
        st.markdown("#### Relación entre precio medio de alquiler y ROI neto por barrio")
        if 'city' in df.columns and df['city'].str.lower().nunique() == 1 and df['city'].str.lower().iloc[0] == 'valencia':
            if 'price' in df.columns and 'Net ROI (%)' in df.columns:
                fig_val = px.scatter(
                    df,
                    x='price',
                    y='Net ROI (%)',
                    color='neighbourhood',
                    hover_data=['neighbourhood'],
                    opacity=0.6,
                    labels={'price': 'Precio alquiler (€)', 'Net ROI (%)': 'ROI Neto (%)', 'neighbourhood': 'Barrio'},
                    title='Relación entre precio de alquiler y ROI neto por barrio (Valencia)'
                )
                fig_val.update_traces(marker=dict(size=10, line=dict(width=1, color='DarkSlateGrey')))
                fig_val.update_layout(
                    legend_title_text='Barrio',
                    showlegend=False,
                    height=500,
                    margin=dict(l=40, r=40, t=60, b=40)
                )
                st.plotly_chart(fig_val, use_container_width=True)
            else:
                st.info("No hay datos suficientes para mostrar el gráfico de dispersión para Valencia.")
        else:
            df_barrio = df.groupby('neighbourhood').agg({'price': 'mean', 'Net ROI (%)': 'mean'}).reset_index()
            if not df_barrio.empty:
                fig_scatter = px.scatter(
                    df_barrio,
                    x='price',
                    y='Net ROI (%)',
                    text='neighbourhood',
                    labels={'price': 'Precio medio alquiler (€)', 'Net ROI (%)': 'ROI Neto (%)'},
                    title='Precio medio de alquiler vs ROI Neto por barrio'
                )
                fig_scatter.update_traces(marker=dict(size=12, color='royalblue', line=dict(width=1, color='DarkSlateGrey')))
                fig_scatter.update_layout(
                    height=500,
                    margin=dict(l=40, r=40, t=60, b=40)
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("No hay datos para mostrar la relación entre precio y ROI.")

        # Número medio de amenities por barrio
        st.markdown("#### Top 15 barrios por número medio de amenities")
        if 'amenities' in df.columns:
            df['n_amenities'] = df['amenities'].str.count(',') + 1
            barrio_amenities = df.groupby('neighbourhood')['n_amenities'].mean().reset_index()
            barrio_amenities = barrio_amenities.sort_values(by='n_amenities', ascending=False).head(15)
            if not barrio_amenities.empty:
                fig_amenities = px.bar(
                    barrio_amenities,
                    x='n_amenities',
                    y='neighbourhood',
                    orientation='h',
                    labels={'n_amenities': 'Nº medio de amenities', 'neighbourhood': 'Barrio'},
                    title='Top 15 barrios por número medio de amenities',
                    color='n_amenities',
                    color_continuous_scale='Purples'
                )
                fig_amenities.update_layout(
                    height=500,
                    margin=dict(l=40, r=40, t=60, b=40),
                    yaxis=dict(tickfont=dict(size=12)),
                    xaxis=dict(tickfont=dict(size=12))
                )
                st.plotly_chart(fig_amenities, use_container_width=True)
            else:
                st.info("No hay datos de amenities para mostrar.")
        else:
            st.info("No hay datos de amenities para mostrar.")

        # Número total de reseñas por barrio
        st.markdown("#### Top 15 barrios por número total de reseñas")
        if 'number_of_reviews' in df.columns:
            barrio_mas_resenas = df.groupby('neighbourhood')['number_of_reviews'].sum().reset_index()
            barrio_mas_resenas = barrio_mas_resenas.sort_values(by='number_of_reviews', ascending=False).head(15)
            if not barrio_mas_resenas.empty:
                fig_resenas = px.bar(
                    barrio_mas_resenas,
                    x='number_of_reviews',
                    y='neighbourhood',
                    orientation='h',
                    labels={'number_of_reviews': 'Número total de reseñas', 'neighbourhood': 'Barrio'},
                    title='Top 15 barrios por número total de reseñas',
                    color='number_of_reviews',
                    color_continuous_scale='Blues'
                )
                fig_resenas.update_layout(
                    height=500,
                    margin=dict(l=40, r=40, t=60, b=40),
                    yaxis=dict(tickfont=dict(size=12)),
                    xaxis=dict(tickfont=dict(size=12))
                )
                st.plotly_chart(fig_resenas, use_container_width=True)
            else:
                st.info("No hay datos de reseñas para mostrar.")
        else:
            st.info("No hay datos de reseñas para mostrar.")

        # Habitaciones y baños por barrio
        st.markdown("#### Top 15 barrios por número medio de habitaciones y baños")
        if 'bedrooms' in df.columns and 'bathrooms' in df.columns:
            barrio_habitaciones_banos = df.groupby('neighbourhood').agg({
                'bedrooms': 'mean',
                'bathrooms': 'mean'
            }).reset_index()
            barrio_habitaciones_banos = barrio_habitaciones_banos.sort_values(by='bedrooms', ascending=False).head(15)
            if not barrio_habitaciones_banos.empty:
                fig_hab = px.bar(
                    barrio_habitaciones_banos,
                    x='bedrooms',
                    y='neighbourhood',
                    orientation='h',
                    labels={'bedrooms': 'Habitaciones medias', 'neighbourhood': 'Barrio'},
                    title='Top 15 barrios por número medio de habitaciones',
                    color='bedrooms',
                    color_continuous_scale='Teal'
                )
                fig_hab.update_layout(
                    height=500,
                    margin=dict(l=40, r=40, t=60, b=40),
                    yaxis=dict(tickfont=dict(size=12)),
                    xaxis=dict(tickfont=dict(size=12))
                )
                st.plotly_chart(fig_hab, use_container_width=True)
            else:
                st.info("No hay datos de habitaciones para mostrar.")
        else:
            st.info("No hay datos de habitaciones o baños para mostrar.")

        # Histograma de precios de alquiler
        st.markdown("#### Histograma de precios de alquiler")
        if 'price' in df.columns:
            fig_hist = px.histogram(
                df, x='price', nbins=40, color='neighbourhood',
                labels={'price': 'Precio alquiler (€)'},
                title='Distribución de precios de alquiler por barrio',
                opacity=0.7
            )
            fig_hist.update_layout(
                height=400,
                margin=dict(l=40, r=40, t=60, b=40),
                xaxis=dict(tickfont=dict(size=12)),
                yaxis=dict(tickfont=dict(size=12)),
                barmode='overlay'
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("No hay datos de precios para mostrar histograma.")

        # Boxplot de precios de alquiler por barrio (solo top 15 barrios)
        st.markdown("#### Boxplot de precios de alquiler por barrio (Top 15)")
        if 'price' in df.columns:
            top_barrios = df['neighbourhood'].value_counts().head(15).index
            df_top = df[df['neighbourhood'].isin(top_barrios)]
            fig_box = px.box(
                df_top, x='neighbourhood', y='price', points='outliers',
                labels={'price': 'Precio alquiler (€)', 'neighbourhood': 'Barrio'},
                title='Boxplot de precios de alquiler por barrio (Top 15)'
            )
            fig_box.update_layout(
                height=500,
                margin=dict(l=40, r=40, t=60, b=40),
                xaxis=dict(tickangle=45, tickfont=dict(size=12)),
                yaxis=dict(tickfont=dict(size=12))
            )
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("No hay datos de precios para mostrar boxplot.")

        # Histograma de ROI Neto
        st.markdown("#### Histograma de ROI Neto (%)")
        if 'Net ROI (%)' in df.columns:
            fig_hist_roi = px.histogram(
                df, x='Net ROI (%)', nbins=40, color='neighbourhood',
                labels={'Net ROI (%)': 'ROI Neto (%)'},
                title='Distribución de ROI Neto por barrio',
                opacity=0.7
            )
            fig_hist_roi.update_layout(
                height=400,
                margin=dict(l=40, r=40, t=60, b=40),
                xaxis=dict(tickfont=dict(size=12)),
                yaxis=dict(tickfont=dict(size=12)),
                barmode='overlay'
            )
            st.plotly_chart(fig_hist_roi, use_container_width=True)
        else:
            st.info("No hay datos de ROI Neto para mostrar histograma.")

        # Boxplot de ROI Neto por barrio (solo top 15 barrios)
        st.markdown("#### Boxplot de ROI Neto por barrio (Top 15)")
        if 'Net ROI (%)' in df.columns:
            top_barrios = df['neighbourhood'].value_counts().head(15).index
            df_top = df[df['neighbourhood'].isin(top_barrios)]
            fig_box_roi = px.box(
                df_top, x='neighbourhood', y='Net ROI (%)', points='outliers',
                labels={'Net ROI (%)': 'ROI Neto (%)', 'neighbourhood': 'Barrio'},
                title='Boxplot de ROI Neto por barrio (Top 15)'
            )
            fig_box_roi.update_layout(
                height=500,
                margin=dict(l=40, r=40, t=60, b=40),
                xaxis=dict(tickangle=45, tickfont=dict(size=12)),
                yaxis=dict(tickfont=dict(size=12))
            )
            st.plotly_chart(fig_box_roi, use_container_width=True)
        else:
            st.info("No hay datos de ROI Neto para mostrar boxplot.")

        # Histograma de días alquilados
        st.markdown("#### Histograma de días alquilados")
        if 'days_rented' in df.columns:
            fig_hist_days = px.histogram(
                df, x='days_rented', nbins=40, color='neighbourhood',
                labels={'days_rented': 'Días alquilados'},
                title='Distribución de días alquilados por barrio',
                opacity=0.7
            )
            fig_hist_days.update_layout(
                height=400,
                margin=dict(l=40, r=40, t=60, b=40),
                xaxis=dict(tickfont=dict(size=12)),
                yaxis=dict(tickfont=dict(size=12)),
                barmode='overlay'
            )
            st.plotly_chart(fig_hist_days, use_container_width=True)
        else:
            st.info("No hay datos de días alquilados para mostrar histograma.")

        # Boxplot de días alquilados por barrio (solo top 15 barrios)
        st.markdown("#### Boxplot de días alquilados por barrio (Top 15)")
        if 'days_rented' in df.columns:
            top_barrios = df['neighbourhood'].value_counts().head(15).index
            df_top = df[df['neighbourhood'].isin(top_barrios)]
            fig_box_days = px.box(
                df_top, x='neighbourhood', y='days_rented', points='outliers',
                labels={'days_rented': 'Días alquilados', 'neighbourhood': 'Barrio'},
                title='Boxplot de días alquilados por barrio (Top 15)'
            )
            fig_box_days.update_layout(
                height=500,
                margin=dict(l=40, r=40, t=60, b=40),
                xaxis=dict(tickangle=45, tickfont=dict(size=12)),
                yaxis=dict(tickfont=dict(size=12))
            )
            st.plotly_chart(fig_box_days, use_container_width=True)
        else:
            st.info("No hay datos de días alquilados para mostrar boxplot.")

        # Mapa de puntos de los anuncios (si hay lat/lon)
        st.markdown("#### Mapa de anuncios")
        if 'latitude' in df.columns and 'longitude' in df.columns:
            st.map(df[['latitude', 'longitude']].dropna())
        else:
            st.info("No hay datos de localización para mostrar el mapa.")

        # Delincuencia: Gráfico de barras agrupadas y heatmap
        st.markdown("#### Delitos denunciados en Valencia por año")
        if df_delincuencia is not None and not df_delincuencia.empty:
            df_delincuencia_filtrado = df_delincuencia[df_delincuencia['Parámetro'] != 'Total']
            fig, ax = plt.subplots(figsize=(14, 7))
            sns.barplot(
                data=df_delincuencia_filtrado,
                x='Año',
                y='Denuncias',
                hue='Parámetro',
                ax=ax
            )
            ax.set_title('Delitos denunciados en Valencia por año')
            ax.set_ylabel('Número de denuncias')
            ax.set_xlabel('Año')
            ax.legend(title='Tipo de delito', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            st.pyplot(fig)

            st.markdown("#### Mapa de calor de delitos denunciados en Valencia por tipo y año")
            fig2, ax2 = plt.subplots(figsize=(14, 7))
            heatmap_data = df_delincuencia_filtrado.pivot_table(
                index='Parámetro',
                columns='Año',
                values='Denuncias',
                aggfunc='sum'
            ).fillna(0)
            sns.heatmap(
                heatmap_data,
                cmap='YlOrRd',
                annot=True,
                fmt='.0f',
                linewidths=.5,
                cbar_kws={'label': 'Número de denuncias'},
                annot_kws={"size": 10},
                ax=ax2
            )
            ax2.set_title('Mapa de calor de delitos denunciados en Valencia por tipo y año')
            ax2.set_xlabel('Año')
            ax2.set_ylabel('Tipo de delito')
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig2)
        else:
            st.info("No hay datos de delincuencia para mostrar.")

    else:
        st.info("No hay datos para mostrar en esta pestaña.")

# ------------------ Pestaña 6: Conclusiones ------------------
with main_tabs[5]:
    st.subheader("Conclusiones finales para empresas interesadas en invertir en alquiler turístico en Valencia (AirBnB)")
    st.markdown("""
El análisis exhaustivo de los datos de rentabilidad, competencia, demanda, precios y características de los barrios de Valencia permite extraer recomendaciones más precisas y accionables para empresas que buscan invertir en el mercado de alquiler turístico:

**Rentabilidad y retorno de inversión:** Los barrios líderes en rentabilidad neta y bruta, como Ciutat Universitaria, Cami Fondo, Penya-Roja y La Roqueta, ofrecen retornos superiores al promedio de la ciudad. Sin embargo, la diferencia entre rentabilidad bruta y neta es relativamente baja en los barrios más rentables, lo que indica una estructura de costes eficiente y un mercado consolidado.

**Demanda sostenida y visibilidad:** Barrios como Cabanyal-Canyamelar, Russafa y El Mercat destacan por su alto volumen de reseñas totales y mensuales, reflejando una demanda turística constante y una elevada rotación de huéspedes. Invertir en estas zonas garantiza visibilidad y ocupación, aunque implica enfrentarse a una competencia intensa.

**Competencia y saturación:** La saturación de anuncios es especialmente alta en barrios turísticos y céntricos. Para destacar en estos mercados, es fundamental apostar por la diferenciación, la calidad del alojamiento y la experiencia del huésped. Por otro lado, existen barrios con alta rentabilidad y baja competencia (menor número de anuncios), que representan oportunidades para captar reservas con menor riesgo de saturación.

**Calidad, amenities y tamaño de la vivienda:** Los barrios con mayor número medio de amenities y viviendas más espaciosas tienden a lograr mejores valoraciones y mayor rentabilidad. La inversión en equipamiento y servicios adicionales puede ser clave para maximizar ingresos y diferenciarse en mercados competitivos.

**Diversidad de precios y accesibilidad:** Valencia presenta una amplia dispersión de precios de alquiler y compra por metro cuadrado, tanto entre barrios como dentro de cada uno. Esto permite adaptar la estrategia de inversión según el presupuesto y el perfil de riesgo, desde zonas premium hasta barrios emergentes con potencial de revalorización.

**Relación entre precio y competencia:** Los barrios con precios de alquiler más altos suelen concentrar también mayor competencia. Sin embargo, existen zonas con precios elevados y menor saturación, que pueden ser especialmente atractivas para inversores que buscan maximizar ingresos sin enfrentarse a una oferta excesiva.

**Factores adicionales:** Es imprescindible monitorizar la evolución de la normativa local, la estacionalidad de la demanda, la seguridad y otros factores externos que pueden impactar la rentabilidad y la sostenibilidad de la inversión.

**Recomendación estratégica:**  
La mejor estrategia combina la selección de barrios con alta rentabilidad neta, demanda sostenida y competencia controlada, junto con una apuesta por la calidad, el equipamiento y la diferenciación. Diversificar la cartera en diferentes zonas y perfiles de barrio permite equilibrar riesgo y retorno. Además, es clave realizar un seguimiento continuo de los indicadores clave del mercado y adaptar la oferta a las tendencias y preferencias de los huéspedes.

En resumen, Valencia ofrece un mercado dinámico y diverso, con grandes oportunidades para empresas de alquiler turístico. El éxito dependerá de una toma de decisiones basada en datos, una gestión activa y una visión integral que combine rentabilidad, demanda, competencia y calidad.
    """)

# ------------------ Descargable ------------------
with st.expander("Ver datos en formato tabla"):
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Descargar datos filtrados (CSV)",
            data=csv,
            file_name="valencia_inmobiliario.csv",
            mime="text/csv",
        )
    else:
        st.info("No hay datos para mostrar o descargar.")

# ------------ Información del dashboard ------------
st.sidebar.markdown("---")
st.sidebar.info("""
**Acerca de este Panel**

Este panel muestra datos del mercado inmobiliario de Valencia, Málaga, Madrid y Barcelona para análisis de inversión.
Desarrollado con Streamlit, Plotly Express y Seaborn.
""")