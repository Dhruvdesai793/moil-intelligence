# Research, Sources and Scientific Limits

## Manganese remote sensing

Singh, Sarkar, Manche, Guha and Kumar (2023), *Earth observation approach for targeting stratiform deposit of manganese in central India*, Advances in Space Research 72, 1094-1108: [DOI](https://doi.org/10.1016/j.asr.2023.03.044).

The relevant approach combines multisensor surface information with geology and ground evidence. A satellite band profile is not a manganese assay. Do not define a universal true manganese wavelength or turn a laboratory curve match into an ore probability. Host minerals, vegetation, moisture, grain size and mixed pixels affect spectra; subsurface reserves require drilling and geological interpretation.

The comparison uses the actual public-domain [USGS splib05a pyrolusite HS138 spectrum](https://pubs.usgs.gov/of/2003/ofr-03-395/ASCII/M/pyrolusite_hs138.5705.asc), documented by Clark et al. 2003, USGS Open-File Report 03-395. [Sample description](https://pubs.usgs.gov/of/2003/ofr-03-395/DESCRIPT/M/pyrolusite_hs138.html): a dry-sieved Colorado sample, not local ore. Source SHA256 is retained; invalid/deleted samples are omitted. The plot overlays native laboratory samples with approximate Sentinel-2A band centers, not a sensor-response convolution. No mineral identification or similarity score is computed.

[USGS Spectral Library version 7](https://www.usgs.gov/labs/spectroscopy-lab/usgs-spectral-library) is a future expanded reference source; the current bundled measurement is explicitly from splib05a, not mislabeled version 7.

## Sausar map and MOIL points

The approximate study envelope is 78.5-80.7 E, 21.1-22.3 N. It is a bounded software study area around the Sausar corridor, not a digitized official geology polygon. Geological context: [Manekar, Shome and Chaudhari 2019](https://doi.org/10.2478/ntpe-2019-0007).

Four historical representative reference points are derived from published official environmental-clearance/mining documents. They are not current verified mine boundaries and should be replaced with authorized lease geometry before operational use:

- [Munsar mining scheme](https://environmentclearance.nic.in/writereaddata/online/EC/140620161J0QBZKYSchemeofMiningMunsar.pdf): published reference point.
- [Kandri ministry minutes](https://environmentclearance.nic.in/viewminutes.aspx?code=MIN&date1=05%2F15%2F2015): published reference point.
- [Chikla pre-feasibility report](https://environmentclearance.nic.in/writereaddata/Online/TOR/30_Nov_2021_16285060029299741PFRChikla.pdf): midpoint of reported coordinate extent, not a lease centroid.
- [Balaghat/Bharweli ministry minutes](https://environmentclearance.nic.in/writereaddata/Form-1A/Minutes/09062017IQEQ38Q4MinutesMergedMayMeeting.pdf): a published boundary reference point.

These are not an exhaustive current MOIL mine inventory. Seeded Nagpur/Bhandara/Balaghat/Dongri demo candidates are independent software fixtures, not confirmed mine/deposit records. User-added locations are unverified candidates.

## Measured feature definitions

| Source | Output | Scaling / support |
| --- | --- | --- |
| [Sentinel-2 SR Harmonized](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED) | B2-B8, B8A, B11, B12 reflectance; NDVI; NDMI | 0.0001 reflectance scaling; native 10/20 m bands |
| [Landsat 8 Collection 2 L2](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2) | Median surface temperature | ST_B10 x 0.00341802 +149 K, minus 273.15; delivered 30 m / thermal native ~100 m |
| [CHIRPS daily](https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHG_CHIRPS_DAILY) | Historical rainfall sum | mm, ~5.6 km; missing days flagged |
| [SMAP L4 v008](https://developers.google.com/earth-engine/datasets/catalog/NASA_SMAP_SPL4SMGP_008) | Median surface/root-zone moisture | m3/m3, ~9 km, three-hourly |
| [SRTM](https://developers.google.com/earth-engine/datasets/catalog/USGS_SRTMGL1_003) | Elevation and slope | 30 m; static historical terrain |

Sentinel-2 SCL excludes no-data, defective pixels, shadows, cloud, cirrus and snow. Temporal medians are sampled in small metric squares (width ~three native pixels) or bounded AOIs. Native source projections are used for reductions. This is an initial neighborhood policy, not a validated optimal extraction radius. It is not guaranteed to be an exact sensor-grid-centered 3x3 pixel window. SCL mask dilation, per-date quality, robust geological masks and preprocessing ablations remain future scientific work.

Coverage is the spatial fraction with valid pixels in the temporal composite, NOT the number/fraction of cloud-free dates. Minimum fraction defaults to 0.6. Sentinel counts can include overlapping tiles; they are not distinct clear acquisition dates. Landsat/terrain/coarse products have simpler null/count checks, not full calibrated quality scores. Mixed S2A/S2B imagery uses approximate S2A centers on the plot; wavelengths are not exact scene-specific instrument responses.

## Audit alignment and exceptions

Preserved: backend-only orchestration, materialized/batch-first GEE, explicit sensor resolution and time metadata, PostGIS spatial storage, staged ML integration, graceful missing components and no fabricated scientific claims.

Not a claim of perfect audit completion: production service-account GEE setup/export-to-cloud, full training ingestion/validation pipeline, specialist trained models, spatial/chronological validation, scientific uncertainty, geology/drill integration and retraining are still absent. Local OAuth and the bounded local worker are the development milestone. The existing user-specified infrastructure milestone was implemented before the audit's complete scientific validation gates; do not confuse application readiness with scientific readiness.

## Future scientifically useful additions

Authorized geological/structural layers, assay and borehole ingestion with units/QA, feature coverage maps, provenance lineage, distinct-date temporal series, preprocessing version enforcement, spatially blocked model evaluation, field outcomes and reviewer feedback. A validated prospectivity layer comes after labelled ground data and model validation, not from coloring NDVI or laboratory resemblance.
