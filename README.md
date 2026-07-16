# LIX Maximum Heat Index Plotter

A Streamlit application that converts official NWS National Digital Forecast Database (NDFD) apparent-temperature grids into polished maximum heat-index maps for WFO New Orleans/Baton Rouge social media posts and emergency-management briefings.

## What it does

- Downloads the lightweight Southern Mississippi Valley NDFD apparent-temperature grids.
- Calculates the maximum value for each local calendar day in `America/Chicago`.
- Provides at least Days 1–3 and normally Days 1–7, depending on NDFD availability.
- Clips the forecast to the LIX land forecast area using the supplied operational boundary files.
- Exports 16:9 social-media graphics or 4:3 briefing graphics at up to 200 dpi.
- Lets the user toggle parish/county boundaries, reference cities, and sampled city values.
- Downloads one PNG or a ZIP containing every available day.

## Run locally

The GRIB reader needs ECMWF ecCodes. On Debian/Ubuntu:

```bash
sudo apt-get install libeccodes-dev
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Create an app from this repository.
2. Set the main file path to `app.py`.
3. Deploy. `packages.txt` installs ecCodes and `requirements.txt` installs the Python dependencies.

No API key or secrets are required. Forecast data come directly from the public NWS NDFD feed.

## Data notes

NDFD Apparent Temperature uses heat index in hot conditions and wind chill in cold conditions. The application groups valid grids by Central local date and takes the daily maximum. The generation timestamp indicates when the app retrieved the files; it is not an NDFD issuance timestamp.

