WITH monthly AS (
    SELECT
        site_code,
        DATE_TRUNC('month', measured_at_gmt) AS month,
        COUNT(*) AS expected_hours,
        COUNT(value) AS recorded_hours,
        AVG(value) AS average_no2
    FROM measurements
    WHERE measured_at_gmt >= '2022-09-01'
      AND measured_at_gmt < '2024-09-01'
    GROUP BY site_code, DATE_TRUNC('month', measured_at_gmt)
),
qualifying AS (
    SELECT *
    FROM monthly
    WHERE recorded_hours >= expected_hours * 0.75
),
paired AS (
    SELECT
        b.site_code,
        b.month AS before_month,
        b.recorded_hours AS before_hours,
        a.recorded_hours AS after_hours,
        b.average_no2 AS before_average,
        a.average_no2 AS after_average
    FROM qualifying b
    JOIN qualifying a
      ON b.site_code = a.site_code
     AND a.month = b.month + INTERVAL '1 year'
    WHERE b.month >= '2022-09-01'
      AND b.month < '2023-09-01'
),
summary AS (
    SELECT
        site_code,
        COUNT(*) AS paired_months,
        SUM(before_average * before_hours)
            / SUM(before_hours) AS before_no2,
        SUM(after_average * after_hours)
            / SUM(after_hours) AS after_no2
    FROM paired
    GROUP BY site_code
    HAVING COUNT(*) >= 9 
)
SELECT
    s.site_code,
    s.site_name,
    s.site_type,
    p.paired_months,
    ROUND(p.before_no2, 2) AS before_no2,
    ROUND(p.after_no2, 2) AS after_no2,
    ROUND(
        100.0 * (p.after_no2 - p.before_no2)
        / NULLIF(p.before_no2, 0), 2
    ) AS percentage_change
FROM summary p
JOIN sites s ON p.site_code = s.site_code
ORDER BY percentage_change;