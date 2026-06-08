# Spec: `run_agent()`

**File:** `agent.py`
**Status:** Partially pre-filled — complete the two blank fields before implementing

---

## Purpose

Orchestrate a single conversational turn for the Plant Advisor agent. Given a user message and the conversation history, call the LLM with available tools, execute any tool calls the LLM requests, and return the final text response.

This is the core of what makes Plant Advisor an *agent* rather than a simple chatbot: the ability to decide which tools to call, use their results to inform its response, and loop until it has everything it needs.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_message` | `str` | The user's current message |
| `history` | `list` | Gradio conversation history — list of `[user_msg, assistant_msg]` pairs |

**Output:** `str`

The agent's final text response for this turn. Should never be empty — if something goes wrong, return a user-readable fallback message.

---

## Design Decisions

*Read `specs/system-design.md` (especially the "How the Groq Tool Calling API Works" section) before reviewing these. Complete the two blank fields before writing any code.*

---

### Messages list structure

The messages list must start with the system prompt, then replay the conversation
history, then add the new user message. Gradio history is a list of `[user, assistant]`
pairs — convert each pair to two API-format dicts:

```python
messages = [{"role": "system", "content": SYSTEM_PROMPT}]

for user_msg, assistant_msg in history:
    messages.append({"role": "user", "content": user_msg})
    if assistant_msg:
        messages.append({"role": "assistant", "content": assistant_msg})

messages.append({"role": "user", "content": user_message})
```

---

### Initial LLM call

Pass the model, the messages list, the tool definitions, and `tool_choice="auto"`
so the LLM can decide whether to call a tool or respond directly:

```python
response = client.chat.completions.create(
    model=LLM_MODEL,
    messages=messages,
    tools=TOOL_DEFINITIONS,
    tool_choice="auto",
)
```

---

### Detecting tool calls in the response

The response object has a `choices` list. Index 0 gives the assistant message.
Check its `tool_calls` attribute — if it's truthy, the LLM wants to call tools:

```python
assistant_message = response.choices[0].message

if not assistant_message.tool_calls:
    # No tool calls — LLM has a final answer
    ...
```

---

### Appending the assistant message

When there are tool calls, append the full assistant message object to `messages`
**before** appending any tool results. The API requires this ordering — a tool
result message must immediately follow the assistant message that requested it:

```python
messages.append(assistant_message)  # must come first
```

---

### Executing and appending tool results

For each tool call, extract the name and arguments, call `dispatch_tool()`, and
append the result as a `"tool"` role message. The `tool_call_id` links this result
back to the specific tool call that requested it:

```python
for tool_call in assistant_message.tool_calls:
    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments)
    tool_result = dispatch_tool(tool_name, tool_args)

    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": tool_result,
    })
```

---

### Loop termination conditions
(a) No tool calls: after each LLM call I check if assistant_message.tool_calls
is falsy. If it is, the LLM is done calling tools and has a final answer,
so I return assistant_message.content right there inside the loop.
(b) MAX_TOOL_ROUNDS hit: the for loop only runs MAX_TOOL_ROUNDS times max.
If the LLM keeps requesting tools and never gives a final answer, the
loop just ends and I return a fallback string so the user gets something
instead of an empty response or a crash.

---

### Extracting the final text response
The final text lives in response.choices[0].message.content — I store that
as assistant_message so I can just return assistant_message.content once
I confirm there are no tool_calls on it.

---

## Implementation Notes

**Trace of a working agent turn (what tools were called and in what order):**
Query: "How often should I water my snake plant in winter?"
Round 1 tool call: lookup_plant({"plant_name": "snake plant"})
Round 2 tool call: get_seasonal_conditions({"season": "winter"})
Final response: Got back the snake plant care data and winter seasonal
tips, then the LLM combined both into a specific watering recommendation.

**What happens when you ask about a plant that isn't in the database?**
lookup_plant comes back with found: False. The agent lets the user know
it couldn't find that plant and tries to give general advice based on
what was described. It doesn't crash or return nothing.

**One thing about the tool call API that surprised you:**
You have to append the assistant message to the messages list BEFORE adding
the tool results, even when the assistant message has no actual text in it.
Felt weird to append a basically empty message but the API needs it to match
the tool results back to the right tool calls.