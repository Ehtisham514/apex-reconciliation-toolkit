# Timesheet duplicate and earnings review

This browser tool compares time records exported from separate timekeeping accounts. It helps identify duplicated shifts and gives a reviewable hours and gross earnings summary.

## Start

Open [the Timesheet Review tool](../tools/timesheet-review.html). Upload one combined CSV containing rows from each source. No records are preloaded. The [blank CSV template](../templates/timesheet_entries.csv) contains only the required headers.

Required columns, in this order or any order:

`employee_id, employee_name, work_date, start_time, end_time, break_minutes, hourly_rate, source`

- Use a stable employee ID that matches across source systems.
- Dates must use `YYYY-MM-DD`; times may use `HH:MM` or `HH:MM:SS`.
- Label each export in `source`, such as the timekeeping account name.
- Enter break length in minutes. A blank break is treated as zero.
- Enter hourly rates in USD. A blank rate leaves hours available but excludes the row's earnings from the gross total.
- Put one time record on each CSV row.

## Matching and review rules

- Exact cross-source duplicates are identified by employee ID, date, start, end and break length. When each matching row comes from a different source, the first row is retained and the other copies are marked as removed from the total.
- Repeated rows from the same source are not automatically deducted. They remain in the total and receive a review flag.
- Partial overlaps are flagged, not removed. Check source records before deciding whether they are duplicate punches or separate work.
- If matching copies have different hourly rates, the shift is counted once for hours, but earnings for that shift are withheld until you resolve the rate difference.
- If end time is earlier than start time, the tool treats the shift as crossing midnight. Equal start and end times are rejected.
- Invalid rows appear in the record review and are excluded from totals.

## Calculation limits

Included hours equal shift duration less the entered break. Gross earnings equal included hours multiplied by the row's hourly rate. The tool does not calculate overtime, premiums, tax withholding, deductions, paid leave, or jurisdiction-specific wage requirements. It is not a payroll system and does not post or edit time records.

All processing occurs in the browser. The tool does not send data to a server. Keep real employee data out of public repositories; the public template has no employee records.
