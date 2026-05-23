"""Category A — reference-attachment rules.

These rules attach reference images to the panel generation call. They
emit NO prompt text. The text directives that say "match the attached
<ref>" live in the match/ category and are emitted by separate match
rules paired with each attach rule.

Each attach rule implements `attached_refs(panel, ctx) -> list[dict]`
returning ref-dict entries with at least kind, path, reason. The
composer / build_plan calls into these rules to build the
refs_to_attach list.

Existing pre-refactor attach logic lives inline in next_panel.py's
build_plan; these rule modules document the contract and provide a
canonical method signature so future refactors can route attachment
through the rule registry. The composer is updated in lockstep.
"""
