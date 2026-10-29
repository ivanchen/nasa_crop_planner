Farmers around the world navigate shifting temperatures, changing rainfall patterns, water shortages, extreme weather, and declining soil health. These pressures make it difficult to choose crop rotations that protect fields, conserve water, and support long‑term resilience. Your challenge is to create a decision‑support tool that uses NASA Earth observations along with local soil information, crop characteristics, and farmer priorities to help farmers explore rotation strategies that could strengthen soil health and adapt their farms to changing conditions.

-------

Ada, ini kumpulan dataset yang cocok untuk tool rotasi tanaman. Hampir semua data NASA butuh akun gratis di [Earthdata Login](https://urs.earthdata.nasa.gov/).

## Data NASA Earth observation

| Kebutuhan | Dataset | URL |
|---|---|---|
| Suhu, curah hujan, radiasi matahari (harian, per titik koordinat) | **NASA POWER** (paling gampang, ada REST API tanpa login) | https://power.larc.nasa.gov/ |
| Curah hujan satelit | **GPM IMERG** | https://gpm.nasa.gov/data/imerg |
| Kelembapan tanah | **SMAP** (L3/L4, termasuk root zone) | https://nsidc.org/data/smap |
| Kesehatan vegetasi | **MODIS NDVI/EVI (MOD13Q1)** | https://lpdaac.usgs.gov/products/mod13q1v061/ |
| Evapotranspirasi / kebutuhan air | **MODIS MOD16A2** | https://lpdaac.usgs.gov/products/mod16a2v061/ |
| Air tanah dan kekeringan | **GRACE-FO** dan GRACE Drought Indicator | https://nasagrace.unl.edu/ |
| Hidrologi permukaan (soil moisture, runoff) | **GLDAS** | https://disc.gsfc.nasa.gov/datasets?project=GLDAS |
| Proyeksi iklim masa depan | **NEX-GDDP-CMIP6** | https://www.nccs.nasa.gov/services/data-collections/land-based-products/nex-gddp-cmip6 |
| Citra resolusi tinggi (30 m) | **HLS (Landsat + Sentinel-2)** | https://lpdaac.usgs.gov/products/hlsl30v002/ |

## Tools untuk eksplorasi dan akses

- Earthdata Search: https://search.earthdata.nasa.gov/
- Worldview (visual cepat): https://worldview.earthdata.nasa.gov/
- Giovanni (analisis time series tanpa coding): https://giovanni.gsfc.nasa.gov/giovanni/
- Contoh API POWER: `https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,PRECTOTCORR&community=AG&longitude=106.8&latitude=-6.2&start=20200101&end=20241231&format=JSON`

## Data pendukung non-NASA (tanah dan tanaman)

- **SoilGrids** (pH, karbon organik, tekstur, global 250 m): https://www.isric.org/explore/soilgrids
- **HWSD** (FAO soil database): https://www.fao.org/soils-portal/data-hub/soil-maps-and-databases/harmonized-world-soil-database-v12/en/
- **FAO EcoCrop / GAEZ** (kebutuhan suhu, air, dan tanah per tanaman): https://gaez.fao.org
- **ESA WorldCover** (tutupan lahan): https://esa-worldcover.org
- **GFSAD** (cropland global): https://lpdaac.usgs.gov/products/gfsad30afcev001/

## Saran alur untuk MVP

POWER (iklim historis) + SMAP (kelembapan tanah) + MODIS NDVI (kondisi lahan) + SoilGrids (tanah) + EcoCrop (karakter tanaman). Lima sumber ini sudah cukup untuk skoring rotasi berdasarkan prioritas petani (hemat air, tahan kekeringan, perbaikan tanah). NEX-GDDP bisa ditambahkan sebagai fitur "skenario iklim 2050".

Karena saya tidak mengecek langsung, beberapa URL produk bisa berubah versi (misal v061 jadi v062). Kalau ada yang 404, cari nama produknya di Earthdata Search.

Mau saya bantu bikin contoh script Python untuk narik data POWER dan SoilGrids sekaligus?