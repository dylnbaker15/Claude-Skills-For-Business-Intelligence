# Sample data (fictional)

`meridian_subscription_events_Q2_2026.csv` is a fictional subscription export for Meridian Journal Group,
the invented publisher all Kymira demos use. No real company, person, or
transaction appears in it. It exists so you can try the skills before trusting
them with your own exports:

    Build me a certified revenue report from sample-data/meridian_subscription_events_Q2_2026.csv,
    every number tied to the file's totals.

It is 537 rows, one row per invoice line: date, region, plan, channel,
invoice id, seats, unit price, line total, and the invoice's total.

## Spoilers: the export is booby-trapped

Read on only after you have run it once. Three real-world pathologies are
planted, each one a mistake that shipped in a real report somewhere before a
rule existed for it:

1. **`invoice_total` repeats on every line of an invoice.** Sum that column
   and revenue comes out to $161,317.00. The reconcilable answer, from
   `line_total` (or `invoice_total` over distinct invoices; both must agree),
   is $78,813.00. The doctrine's rule 9: a platform's own numbers are
   claims, not facts.
2. **One line carries a 100x decimal slip** (a Newsroom Pro price entered as
   5900.00). An outlier scan should flag it, and the report should say so
   rather than silently absorb it. Revenue with that line corrected:
   $49,608.00.
3. **The filename says Q2, the contents do not.** A few rows are early July,
   and some dates are US-format among the ISO dates. Rule 4: filenames lie;
   the contents decide the period. Q2-only revenue, corrected:
   $49,394.00.

A Kymira-equipped agent should surface all three unprompted: recompute totals
two independent ways, flag the outlier instead of guessing, and report the
actual date span it found. If yours did, that is the product working.
