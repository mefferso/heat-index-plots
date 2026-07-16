import unittest
from datetime import date, datetime, timezone

import numpy as np

from heat_index.data import ForecastGrid, daily_maxima, nearest_grid_value
from heat_index.map_renderer import cwa_mask, render_map


def synthetic_grid():
    longitude, latitude = np.meshgrid(np.linspace(-92.0, -88.2, 90), np.linspace(28.6, 31.7, 75))
    base = 99 + (longitude + 90.1) * 2.2 + (latitude - 30.0) * 1.7
    values = np.stack((base, base + 3, base + 1, base + 5))
    times = np.array(
        ["2026-07-16T12:00", "2026-07-16T21:00", "2026-07-17T12:00", "2026-07-17T21:00"],
        dtype="datetime64[m]",
    )
    return ForecastGrid(longitude, latitude, values, times, datetime.now(timezone.utc), ("test",))


class CoreTests(unittest.TestCase):
    def test_daily_maxima_and_nearest_value(self):
        forecast = synthetic_grid()
        days = daily_maxima(forecast)
        self.assertEqual([item.day for item in days], [date(2026, 7, 16), date(2026, 7, 17)])
        self.assertTrue(np.allclose(days[0].values_f, forecast.values_f[1]))
        value = nearest_grid_value(forecast.longitude, forecast.latitude, days[0].values_f, -90.0, 30.0)
        self.assertTrue(100 < value < 104)

    def test_cwa_mask_and_png_render(self):
        forecast = synthetic_grid()
        selected = daily_maxima(forecast)[0]
        mask = cwa_mask(forecast.longitude, forecast.latitude)
        self.assertTrue(mask.any())
        self.assertTrue((~mask).any())
        png = render_map(
            forecast.longitude,
            forecast.latitude,
            selected.values_f,
            selected.day,
            forecast.generated_at,
            dpi=100,
        )
        self.assertTrue(png.startswith(b"\x89PNG"))
        self.assertGreater(len(png), 100_000)


if __name__ == "__main__":
    unittest.main()
