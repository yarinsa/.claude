# Analysis

DB: `"$IEC_DATA_DIR/iec.db"` (default `~/Library/Application Support/iec-meter/iec.db`). Open it with `sqlite3`, pandas (`pd.read_sql`), or DuckDB (`ATTACH '<path>' (TYPE sqlite)`).

## Schema

`readings(meter, ts_utc, ts_local, kwh, kwh_export, status, source, fetched_at)`, primary key `(meter, ts_utc)`.

- `ts_utc` is `YYYY-MM-DDTHH:MM:SSZ`, the start of the interval.
- `ts_local` is `YYYY-MM-DD HH:MM`, Asia/Jerusalem wall clock.
- `kwh` is the energy used in that 15-minute interval. Multiply by 4 for average kW.

`imports(source, ref, first_local, last_local, rows, imported_at)` logs every CSV import and every API day.

Views:

| View | Columns |
|---|---|
| `hourly` | `meter, hour_local, kwh, intervals` |
| `daily` | `meter, day, kwh, peak_kw, intervals` (`intervals < 96` means a partial day) |
| `monthly` | `meter, month, kwh, days` |
| `load_profile` | `meter, weekday (0=Sun), hour, avg_kw, samples` |

Rules: group by `ts_local`, and order or diff by `ts_utc`. Treat missing intervals as missing, not zero (`iec status` lists them).

## Ready queries

```sql
-- Monthly totals, with the same month a year earlier
SELECT a.month, ROUND(a.kwh) kwh, ROUND(b.kwh) kwh_last_year
FROM monthly a LEFT JOIN monthly b
  ON b.month = printf('%04d-%s', substr(a.month,1,4) - 1, substr(a.month,6,2))
ORDER BY a.month;

-- Base load: the always-on draw, taken as the 5th percentile of 15-min kW per month
SELECT month, ROUND(kw, 2) AS base_kw FROM (
  SELECT substr(ts_local,1,7) month, kwh*4 kw,
         ROW_NUMBER() OVER (PARTITION BY substr(ts_local,1,7) ORDER BY kwh) rn,
         COUNT(*)     OVER (PARTITION BY substr(ts_local,1,7)) n
  FROM readings) WHERE rn = CAST(n*0.05 AS INT) + 1 ORDER BY month;

-- Top 10 peak intervals
SELECT ts_local, ROUND(kwh*4, 2) kw FROM readings ORDER BY kwh DESC LIMIT 10;

-- Average daily curve, summer vs winter (kW by hour)
SELECT CAST(substr(ts_local,12,2) AS INT) hour,
       ROUND(AVG(CASE WHEN substr(ts_local,6,2) IN ('06','07','08') THEN kwh END)*4, 2) summer_kw,
       ROUND(AVG(CASE WHEN substr(ts_local,6,2) IN ('12','01','02') THEN kwh END)*4, 2) winter_kw
FROM readings GROUP BY hour ORDER BY hour;

-- Weekday vs weekend (Fri, Sat) daily use
SELECT CASE WHEN strftime('%w', day) IN ('5','6') THEN 'Fri/Sat' ELSE 'Sun-Thu' END part,
       ROUND(AVG(kwh), 1) avg_kwh_per_day
FROM daily WHERE intervals >= 92 GROUP BY part;

-- Share of consumption in a time window (e.g. 23:00-07:00)
SELECT ROUND(100.0 * SUM(CASE WHEN substr(ts_local,12,5) >= '23:00' OR substr(ts_local,12,5) < '07:00'
                              THEN kwh END) / SUM(kwh), 1) AS night_pct
FROM readings WHERE ts_local >= date('now','-365 days');
```

## Supplier plans

`iec plans` applies each plan's windows to every 15-minute interval and prints the effective discount as a % of energy. Copy `plans.example.json`, fill in current offers from the suppliers' sites, and run `iec plans --file my-plans.json --from 2025-10-01 --to 2026-10-01`.

Rules for interpreting the result:

- Use a full 12 months, because summer air conditioning and winter heating shift the curve.
- Discounts apply to the energy charge only. Fixed distribution and supply fees are the same at every supplier.
- A window is matched against each interval's own weekday. "Sun–Thu 23:00–07:00" therefore counts Sunday 00:00–07:00 and not Friday 00:00–07:00. Check each supplier's exact definition.

## Spotting appliances

Recurring fixed-time spikes in `load_profile`, such as a jump at 05:00 and 16:00 in both seasons, usually mean a timer-driven load like a water heater (דוד חשמל). Compare `avg_kw` at that hour with its neighbours to estimate its draw. A base load that rises in summer points to air conditioning or refrigeration.
