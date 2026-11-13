**Filter after search: leaks**

1. Query
2. Search whole index: all clients, all teams
3. Top-k chunks: incl. other clients’ (another client’s commercials, already inside the model context)
4. Filter results: too late, already read

**Filter before search: safe**

1. Query
2. Resolve permissions: client/team/user/tier
3. Search scoped index: permitted data only
4. Answer: nothing the user can’t see

The only edge that moves is where the permission check sits. That is the whole difference.
