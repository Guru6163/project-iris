# Deterministic fixtures

Small, hand-authored dataset for **IN (KA)**, **DE (BE/BY)**, and **US (VA)**. Geometries are placed so pilot queries return meaningful overlaps and proximity results.

| File | Contents |
| --- | --- |
| `source_run.sql` | One succeeded run (`source_run_id = 1`) |
| `parcel.sql` | 3 parcels (one per country) |
| `substation.sql` | 3 substations near each parcel |
| `peatland.sql` | 3 peatlands (IN overlaps parcel; DE in BY; US overlaps VA parcel) |
| `screening_layer.sql` | 4 derived layers (IN peat + BESS, DE BESS, US peat) |
| `evidence.sql` | 7 evidence rows linking layers to entities |
| `staging_parcel.sql` | Separate staging batch (`ingest_run_id = 1`) for promotion demo |

All inserts use `ON CONFLICT DO NOTHING` so re-running seeds is idempotent.
