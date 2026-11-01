SELECT
    site_code,
    YEAR(measured_at_gmt) AS year,
    COUNT(*) AS expected_hours,
    COUNT(value) AS recorded_hours,
    ROUND(100.0 * COUNT(value) / COUNT(*), 2) AS completeness_pct,
    ROUND(AVG(value), 2) AS average_no2
FROM measurements
GROUP BY site_code, YEAR(measured_at_gmt)
ORDER BY site_code, year;
