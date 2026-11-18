# Screen map

The clickable plan is `docs/wireframes/index.html`. Open that file in a browser. It is a wireframe, not the application: buttons do not call an API.

Visual rules for the real UI in Phase 1: cream background, forest green accent, system font, compact tables, visible empty/loading/error states, keyboard focus, and the exact badge text `Reference target – not verified` on sheet rows. No sample KPI numbers.

| Route | Phase | Who | Shows | Empty / error |
| --- | --- | --- | --- | --- |
| `/login` | 1 | Signed-out staff | Email and password via Supabase Auth | Invalid credentials stay on the form |
| `/overview` | 1 shell, 8 counts | All roles | Tiles from SQL counts | Em dash and "not connected" until the API answers; then real zeros are allowed because they came from a query |
| `/research` | 3 | Researcher, manager, admin. Sales and read-only can view runs | Filters, budget, run list, DEMO or LIVE badge, candidate review | No key: DEMO fixtures. Provider error: the error, plus retry. Approve does not add a contact |
| `/research/runs/[id]` | 3 | Same | Queries, sources, cost, cancel | Missing run: 404 |
| `/accounts` | 2 | All except hidden writes for read-only | Companies, hypotheses, owner, stage | No rows copy, not a fake company |
| `/accounts/[id]` | 2 | Same | Evidence, products, contacts, notes, audit | Contacts may be absent |
| `/imports` | 2 | Researcher, manager, admin | Mapping, preview, conflicts, result | Row errors listed; nothing committed until confirm |
| `/contacts` | 2 manual, 5 permission | Sales, researcher, manager, admin | Role, source, permission, DNC | Unknown permission: do not call |
| `/calling` | 6 demo, 7 live off | Sales, manager, admin | Queue of permitted contacts only | DEMO badge. Live flag off. Read-only and researcher have no authorize action |
| `/calls/[id]` | 6 | Same, plus read-only view | State, insight, human review, CRM history | Transcript hidden without consent |
| `/crm` | 2 | Sales, manager, admin; read-only view | Kanban and table, stage reason | Outreach Eligible disabled without permission |
| `/tasks` | 2, richer in 8 | Assignee and managers | Due date, owner, status | No tasks |
| `/reports` | 8 | Manager, admin, read-only | Funnel, source yield, cost, ageing, opt-outs | Empty chart state. No decorative series |
| `/settings` | 1 roles stub, full later | Admin | Taxonomy, models, budgets, retention, audit | Secrets are references, never raw values |

Account detail and call detail are linked from the list screens. They are in the wireframe nav so the plan is reviewable without data.
