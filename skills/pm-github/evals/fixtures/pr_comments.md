# PR Review Comment Fixtures for Classification Testing

## Actionable Comments (should produce issues)

### Critical Severity
- "This causes a production outage - data loss on user records"
- "SECURITY: SQL injection vulnerability in user search endpoint"
- "CRITICAL: Authentication bypass allows admin access without credentials"
- "This is a blocker for release - the payment flow is completely broken"
- "RCE vulnerability in file upload - needs immediate fix"

### High Severity
- "The checkout flow fails silently when inventory is empty"
- "Major performance regression - API latency increased 5x"
- "Accessibility violation: missing ARIA labels on all form inputs"
- "Memory leak in background worker - OOM kills after 2 hours"
- "Core user journey broken: can't reset password"

### Medium Severity
- "Consider adding pagination to this endpoint for large datasets"
- "This function is doing too much - should be split into smaller units"
- "Missing error handling for network timeout case"
- "Type hints are incomplete for public API functions"
- "Inconsistent naming convention with the rest of the codebase"

### Low Severity
- "nit: trailing whitespace on line 42"
- "nitpick: prefer single quotes for consistency"
- "Unused import on line 15"
- "Could simplify this ternary expression"
- "Missing period in comment"

## Non-Actionable Comments (should NOT produce issues)

### Approvals/Praise
- "LGTM! 👍"
- "Looks good to me, ship it"
- "Great work on this refactor!"
- "Approved"
- "Nice cleanup ✨"

### Questions/Discussion
- "Why did you choose this approach over X?"
- "What's the performance impact of this change?"
- "I'm curious about the design decision here"
- "Could you explain this logic?"
- "Have you considered using library Y instead?"

### Suggestions (non-blocking)
- "Might be worth adding a test for the edge case"
- "Consider extracting this to a utility function"
- "This could be simplified with a list comprehension"
- "Maybe we should add a comment here"
- "I'd prefer if we used a different variable name"

## Mixed/Ambiguous Comments

### Medium + needs-triage (default fallback)
- "This looks weird but I'm not sure why"
- "Something feels off about this implementation"
- "Not sure if this handles all cases"
- "Could be a bug but need to investigate"

### High + enhancement
- "This would be much better with a caching layer"
- "We should really add support for webhooks here"
- "Feature request: add dark mode toggle"

---

## Expected Classification Results

| Comment | Severity | Type | Actionable |
|---------|----------|------|------------|
| "This causes a production outage" | Critical | bug | Yes |
| "SECURITY: SQL injection" | Critical | security | Yes |
| "nit: trailing whitespace" | Low | needs-triage | Yes |
| "LGTM!" | Low | non-actionable | No |
| "Why did you choose this?" | Low | non-actionable | No |
| "Missing error handling" | Medium | bug | Yes |
| "Consider adding pagination" | Medium | enhancement | Yes |
| "We should add caching" | High | enhancement | Yes |
| "Something feels off" | Medium | needs-triage | Yes |
| "Approved" | Low | non-actionable | No |