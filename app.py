from __future__ import annotations

import io
import zipfile
from datetime import datetime

import streamlit as st

from heat_index.data import daily_maxima, load_forecast
from heat_index.map_renderer import render_map


st.set_page_config(page_title="LIX Heat Index Plotter", page_icon="🌡️", layout="wide")
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1500px;}
    [data-testid="stSidebar"] {background: #f4f7fa;}
    .source-note {color: #5d6b76; font-size: .86rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=1800, show_spinner=False)
def get_forecast():
    forecast = load_forecast()
    return forecast, daily_maxima(forecast)


st.title("LIX Maximum Heat Index Plotter")
st.caption("Official NWS/NDFD apparent-temperature forecasts formatted for social media and EM briefings.")

with st.sidebar:
    st.header("Map controls")
    if st.button("Refresh NDFD forecast", use_container_width=True):
        get_forecast.clear()
        st.rerun()

try:
    with st.spinner("Loading the latest NDFD apparent-temperature grids…"):
        forecast, days = get_forecast()
except Exception as error:
    st.error("The latest NDFD grid could not be loaded.")
    st.exception(error)
    st.info("Try **Refresh NDFD forecast** in a minute. NOAA occasionally replaces a GRIB file during an update.")
    st.stop()

if not days:
    st.error("NDFD returned no forecast days.")
    st.stop()

with st.sidebar:
    selected_day = st.selectbox(
        "Forecast day",
        options=range(len(days)),
        format_func=lambda index: f"Day {index + 1} — {days[index].day.strftime('%a %b')} {days[index].day.day}",
    )
    output_format = st.selectbox("Output format", ("Social media (16:9)", "EM briefing (4:3)"))
    title = st.text_input("Main title", "Maximum Heat Index")
    subtitle = st.text_input("Subtitle (optional)", "")
    st.divider()
    show_cities = st.toggle("Show reference cities", True)
    city_detail = st.selectbox("City detail", ("Key cities", "All reference cities"), disabled=not show_cities)
    show_values = st.toggle("Show city value panel", True, disabled=not show_cities)
    show_counties = st.toggle("Show parish/county lines", True)
    dpi = st.select_slider("Export quality", options=(100, 150, 200), value=150, format_func=lambda x: f"{x} dpi")

selected = days[selected_day]
png = render_map(
    forecast.longitude,
    forecast.latitude,
    selected.values_f,
    selected.day,
    forecast.generated_at,
    title=title or "Maximum Heat Index",
    subtitle=subtitle,
    show_cities=show_cities,
    show_city_values=show_values,
    show_counties=show_counties,
    city_detail=city_detail,
    format_name=output_format,
    dpi=dpi,
)

st.image(png, use_container_width=True)

filename = f"lix_max_heat_index_{selected.day.isoformat()}.png"
left, right = st.columns([1, 1])
with left:
    st.download_button(
        "Download current PNG",
        data=png,
        file_name=filename,
        mime="image/png",
        use_container_width=True,
        type="primary",
    )
with right:
    if st.button("Build all forecast days (.zip)", use_container_width=True):
        archive_buffer = io.BytesIO()
        with st.spinner("Rendering every available forecast day…"):
            with zipfile.ZipFile(archive_buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for item in days:
                    image = render_map(
                        forecast.longitude,
                        forecast.latitude,
                        item.values_f,
                        item.day,
                        forecast.generated_at,
                        title=title or "Maximum Heat Index",
                        subtitle="",
                        show_cities=show_cities,
                        show_city_values=show_values,
                        show_counties=show_counties,
                        city_detail=city_detail,
                        format_name=output_format,
                        dpi=dpi,
                    )
                    archive.writestr(f"lix_max_heat_index_{item.day.isoformat()}.png", image)
        st.download_button(
            "Download forecast package",
            data=archive_buffer.getvalue(),
            file_name=f"lix_heat_index_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
            mime="application/zip",
            use_container_width=True,
        )

with st.expander("Forecast and data details"):
    st.write(
        f"Available range: **{days[0].day.strftime('%B %d')}–{days[-1].day.strftime('%B %d, %Y')}** "
        f"({len(days)} local calendar days). Selected day uses {selected.sample_count} forecast grids."
    )
    st.markdown(
        "Source: [National Digital Forecast Database — Apparent Temperature]"
        "(https://tgftp.nws.noaa.gov/SL.us008001/ST.opnl/DF.gr2/DC.ndfd/AR.smissvly/). "
        "Daily maxima are calculated by local calendar day in America/Chicago."
    )
