# Evidence of interest and use

This project invites independent reproduction and technical feedback. A public release alone does not demonstrate adoption. Stars record interest; visitors, clones, forks, and notebook opens do not establish successful reproduction or operational use.

## Record outcomes precisely

| Evidence | What it supports | What it does not establish |
| --- | --- | --- |
| Star, page visit, or clone | Recorded interest or access | Successful use, endorsement, or scientific validity |
| Contributor's reproduction report with environment and observed metrics | A documented attempt or successful saved-output reproduction, as reported | Fresh-data validation or a building-control result |
| Reviewed outside pull request | A concrete external contribution | Adoption by the contributor's organization |
| Independent extension with code and a linked result | The specific documented extension | Generalization beyond the new experiment |
| Measured field study with equipment, timing, comfort, and counterfactual evidence | Its supported operational outcomes | Savings or safety for other buildings |

Reproduction reports should name the exact commit or source hashes, environment, commands, and observed outputs. Report failures alongside successes. State whether a report is contributor-reported or checked by the maintainers. Keep identities and quotes public only with the contributor's permission.

## Owner-only traffic snapshots

GitHub retains rolling visitor and clone information for the past 14 days. Save dated snapshots while evaluating a release. The repository's own tests and the owner's visits can contribute to traffic, so these counts are descriptive. GitHub's [traffic documentation](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-traffic-to-a-repository) explains availability and update times.

With an already authenticated GitHub CLI, run:

```bash
python3 scripts/capture_impact.py --output local-impact
```

`local-impact/` is gitignored. You may instead specify a private directory outside the repository. The script reads stars, forks, subscribers, open issues, and the available traffic endpoints. It records access failures explicitly. It does not publish the snapshot, obtain new permissions, or add analytics to the demo.

## Suggested first-week activities

Invite three independent reproduction attempts, share one factual explanation with a relevant community that permits project posts, and follow up on specific technical feedback. These are activities to attempt, not promised outcomes or existing impact. Count completed reports and contributions separately from invitations sent.

Before outreach, confirm the target venue's review/publicity requirements and avoid sending a submission to a known assigned reviewer. Do not buy stars, arrange reciprocal stars, create artificial accounts, or describe requested stars as independent adoption. A modest number of documented useful interactions is sufficient to report honestly.
