1. **Inbound record:** email / call / chat
2. **Deterministic match:** domain · address · ID. cheap, exact, incomplete
   - hit: **Canonical person + organisation**
   - miss: **Probabilistic match:** name variants, signature, embedding similarity
3. **Probabilistic match**
   - above threshold: **Canonical person + organisation**
   - otherwise: **Review queue** (keep this small, or it becomes manual tagging)

**BREAKS NAIVE MATCHING**

- two clients, one parent co.
- a contact moves firms
- your staff on client domains
- shared inboxes & lists

each one is its own rule
