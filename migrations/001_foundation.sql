-- Foundation: PostGIS extension and IRIS schemas.
-- Business tables are added in later migrations.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS iris_staging;
CREATE SCHEMA IF NOT EXISTS iris_core;
