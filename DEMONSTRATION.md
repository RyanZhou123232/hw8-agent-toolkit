# Demonstration

I tested the toolkit on two tasks involving my existing application-tracking spreadsheet. The goal was to check whether an agent could retrieve real records, produce an accurate summary, and have that summary reviewed independently.

The doing agent used Codex Work with an explicit command-line MCP client. It discovered the server’s tool catalog and called `application_tracker` through the actual stdio server. Native Codex integration was not confirmed.

Each result went to a separate checker session with a fresh context. The reviewer received the task requirements, returned data, and relevant source files, without the doing agent’s conversation or an expected verdict.

Private application details are omitted below. Redaction markers represent removed values, not the arguments originally sent.

## Run 1: Applications to one organization

The first task was to summarize applications to a particular organization.

The agent called:

```json
{
  "name": "application_tracker",
  "arguments": {
    "action": "query",
    "company": "[REDACTED]",
    "limit": 100
  }
}
```

The query returned three matches with `truncated: false`. Two belonged to the intended organization. The third belonged to another company whose name happened to contain the search substring.

The agent excluded that third record from the organization’s application count. It also described the statuses as information recorded in the spreadsheet, without treating them as confirmation of new interviews or employer decisions.

The fresh checker accepted all six task criteria. It compared the summary with the returned records, repeated the query, and independently confirmed that the original workbook’s hash had not changed.

## Run 2: Applications matching a role and status

The second task was to find applications matching both a role-title substring and a recorded status.

```json
{
  "name": "application_tracker",
  "arguments": {
    "action": "query",
    "title": "[REDACTED]",
    "status_filter": "[REDACTED]",
    "limit": 100
  }
}
```

This query returned four matches with `truncated: false`. The agent included all four, preserved the original company spelling, and explained that relevant roles outside the title filter were outside this particular selection.

A different fresh-context checker accepted all six task criteria. It repeated the query, corroborated the returned records, and confirmed an unchanged workbook hash.

Neither task updated the original spreadsheet, submitted an application, or contacted anyone.

## What these runs established

Both runs demonstrated the same workflow: retrieve data through MCP, produce a bounded summary, and review it in a separate session.

They established that the two summaries matched the retrieved records. They did not establish that every update operation was correct. A separate component review later found a preservation bug in the update path, described in [ITERATION.md](ITERATION.md).

The public evidence is redacted, while the original call records and detailed reviews remain private.


## Separate component and skill checks

A fresh agent selected the trivial ping from custom-client metadata, loaded it
through the client and returned exactly `HW8-SKILL-PING: LOADED`. A later fresh
agent selected/loaded acceptance-check the same way and reviewed the entire MCP
component: eight criteria MET, eight tests passed, and a real-workbook-copy wire
query/update/requery preserved original bytes. Native automatic skill discovery
remains unconfirmed; the late probe does not retroactively satisfy setup order.

A separate review also caught a preservation bug after the original seven
tests passed. [ITERATION.md](ITERATION.md) records the genuine failing cases and
fix; passing read-only summaries did not prove updates correct.

