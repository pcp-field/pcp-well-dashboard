"""Pure analysis functions shared by the interface and tests."""
import csv
import io
import math
import statistics

REQUIRED = ['well_name', 'wear_rate', 'pump_speed_rpm', 'tubing_liner_source']
LINERS = ['HDPE Liner', 'No Liner/Coating']
OPTIONAL_NUMERIC = ['rod_torque_load_pct', 'rod_stress_pct', 'produced_rate_m3_day', 'max_dogleg_deg_30m']


def load_rows(raw):
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError('File size must not exceed 5 MB.')
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise ValueError('Save the file as a UTF-8 CSV.') from None
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []
    if len(headers) != len(set(headers)):
        raise ValueError('Duplicate column names are not allowed.')
    missing = set(REQUIRED) - set(headers)
    if missing:
        raise ValueError('Missing required columns: ' + ', '.join(sorted(missing)))
    rows, seen = [], set()
    for line, source in enumerate(reader, 2):
        if len(rows) >= 10000:
            raise ValueError('The maximum is 10,000 wells.')
        if None in source:
            raise ValueError(f'Row {line}: More values than columns.')
        r = {k: (v or '').strip() for k, v in source.items()}
        name = r['well_name']
        if not name or len(name) > 100 or name.casefold() in seen:
            raise ValueError(f'Row {line}: Well name is missing, duplicated, or longer than 100 characters.')
        seen.add(name.casefold())
        if r['tubing_liner_source'] not in LINERS:
            raise ValueError(f'Row {line}: Liner must be HDPE Liner or No Liner/Coating.')
        for field in ['wear_rate', 'pump_speed_rpm'] + OPTIONAL_NUMERIC:
            if field not in r or (field in OPTIONAL_NUMERIC and not r[field]):
                continue
            try:
                value = float(r[field])
            except ValueError:
                raise ValueError(f'Row {line}: Value {field} is not numeric.') from None
            if not math.isfinite(value) or value < 0:
                raise ValueError(f'Row {line}: {field} must be finite and non-negative.')
            r[field] = value
        rows.append(r)
    if not rows:
        raise ValueError('The file has no well records.')
    return rows


def summary(rows):
    if not rows:
        return None
    return dict(count=len(rows), mean_wear=statistics.mean(r['wear_rate'] for r in rows),
                mean_speed=statistics.mean(r['pump_speed_rpm'] for r in rows),
                zero_count=sum(r['wear_rate'] == 0 for r in rows))


def rank(rows, count=5, descending=True):
    # Alphabetical order breaks ties consistently.
    return sorted(rows, key=lambda r: ((-1 if descending else 1) * r['wear_rate'], r['well_name']))[:count]


def groups(rows):
    return {liner: summary([r for r in rows if r['tubing_liner_source'] == liner]) for liner in LINERS}


def csv_bytes(rows):
    stream = io.StringIO()
    if not rows:
        return b''
    w = csv.DictWriter(stream, fieldnames=list(rows[0]), extrasaction='ignore')
    w.writeheader()
    for row in rows:
        # Prevent spreadsheet formula execution when exported CSV is opened in Excel.
        safe = {k: "'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@', '\t', '\r')) else v for k, v in row.items()}
        w.writerow(safe)
    return stream.getvalue().encode('utf-8-sig')
