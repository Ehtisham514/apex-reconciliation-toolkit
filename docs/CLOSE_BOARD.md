# Month-end close board

The close board is a browser-based tracker for close tasks by entity and period. It begins empty; there are no preloaded sample companies or tasks.

## Use the board

Open [the Month-End Close Board](../tools/close-board.html). Add tasks individually or import a CSV checklist. The [blank import template](../templates/month_end_close_board.csv) contains only the expected headers.

Required columns for import:

`entity, period, task`

Optional columns:

`owner, due_date, status, evidence, notes`

Use a period such as `2026-11`. Accepted statuses are Not started, In progress, Blocked, Ready for review, Approved and Not applicable. An unrecognized or blank status imports as Not started. Imports add tasks to the current list; they do not replace existing entries.

Filter by entity, period, status or search text. Update status in the table. Export the visible tasks to CSV for a backup or handoff.

## Data handling and boundaries

Tasks are saved in browser local storage on the current device. They are not uploaded, synced, or backed up by this tool. Export before clearing browser data or changing devices. Do not place confidential details in task notes; store source records in the organization's approved records system and use only an appropriate evidence reference here.

This board does not store evidence files, send reminders, enforce reviewer permissions, integrate with accounting software, or independently verify approvals. An Approved status records the user's entry; it is not evidence that a separate reviewer completed the work.
