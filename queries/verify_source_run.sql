-- Latest successful run per source (requires seed or real data).
SELECT DISTINCT ON (source_id)
    source_run_id,
    source_id,
    source_date,
    status,
    completed_at
FROM iris_core.source_run
WHERE status = 'succeeded'
ORDER BY source_id, source_date DESC, source_run_id DESC;

-- Run inventory by status.
SELECT status, COUNT(*) AS run_count
FROM iris_core.source_run
GROUP BY status
ORDER BY status;
