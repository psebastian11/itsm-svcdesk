<!-- ai-generated: 10% - Policy definitions -->
# Agent Tool Disallow Policy

- Bash(rm *): the reviewer reads and comments; deleting files is the author's decision, not the reviewer's
- Bash(git push *): pushing commits publishes repository state and modifies remote history, which requires explicit developer review
- Bash(docker *): executing container commands alters system daemon state and should only be triggered by the build orchestrator
