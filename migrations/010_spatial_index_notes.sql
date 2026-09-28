-- Document GiST index intent (no new indexes; pilot-driven audit).

COMMENT ON INDEX iris_core.substation_geom_gix IS
    'BESS screening: ST_DWithin / proximity filters on substation points.';
COMMENT ON INDEX iris_core.peatland_geom_gix IS
    'Peatland inference: ST_Intersects against parcel (and peatland-driven joins).';
COMMENT ON INDEX iris_core.parcel_geom_gix IS
    'Both pilots: parcel polygons in intersect and proximity workflows.';
COMMENT ON INDEX iris_core.screening_layer_geom_gix IS
    'Derived screening footprints intersected with parcels (post-screen QA).';
