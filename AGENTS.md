# AGENTS.md

This repository is the **HOME** pack for PCB/schematic style standardization
(`wellmanifest/pcb`).

HOME vs ADOPT: `HOME wellmanifest`, `shape domain_pack`. EDA viewers, digital
threads and CI runners (e.g. `maskservice/viewer`, `digitaltwin-run/twinstudio`)
**ADOPT** this pack. They must not keep a second style SSOT as constants in
their own source.

Closed vocabulary: `HOME` wellmanifest|subactor|semcod;
`SHAPE` domain_pack|runtime_service|both; `ADOPT` wellmanifest/pcb.

The rule vocabulary is closed as well. An adopter that needs a new rule adds it
here first — a profile naming an unknown rule must fail loudly, never degrade
into a rule that silently does nothing.

This pack is **propose-only**: it describes the profile document, the rule
vocabulary and the regression gate. It does not modify KiCad sources, does not
route copper and does not replace DRC or ERC — those stay required gates after
any accepted change.

Prefer `$id` host `https://wellmanifest.com/schemas/...` (no release tags in `$id`).
