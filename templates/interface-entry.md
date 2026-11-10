### [Name]
- Path: [file where the name is defined]
- Name: [Name, identical to the heading]
- Type: [one of: public function, public method, public class, public type, public constant, endpoint, command]
- Input: [parameters with types, and N/A when none]
- Output: [return value with type, and N/A when none]
- Description: [required observable behavior: results for valid input, error cases, edge cases]

Note: only public names get an entry. Everything else is the agent's own design and is not listed. Path may be N/A for any Type when no single file defines the name.
Note: repeat this block once per public name, in the Expected Interface section of the prompt.
