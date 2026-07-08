# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

#User needs to add a pet
    Each user can have multiple pets (one to many)

#User can set options on level of care:
    - maybe they only need help with walks or feeding, OR even all of the above (walk, feeding, meds, enrichment, grooming, etc.)
    -schedule any of these or all
    
#Plan generated for fulfilling all tasks ( a schedule of sorts) can be based on input of user's constrants
    -What time does the user have to work?
    -What time are their hobbies/free time?
    -Do pets get along with each other? (if multiple)
    -


- What classes did you include, and what responsibilities did you assign to each?

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

**c. AI Strategy**

*Which AI coding assistant features were most effective for building your scheduler?*

- **The assistant running my code itself.** The single biggest one. It executed
  `main.py` and drove the Streamlit UI headlessly with `AppTest`, so claims like
  "this works" came with actual terminal output as proof. That's how the
  Streamlit bug got caught and confirmed instead of shipped.
- **Incremental, conversational refactoring.** I added capabilities one at a time
  — `sort_by_time()`, then `filter_tasks()`, then the recurrence logic in
  `mark_complete()` — and each slotted into the existing class structure without
  a rewrite. Building up piece by piece kept me in control of the design.
- **On-demand explanations of Python internals.** When I didn't understand
  `field(default=None, compare=False, repr=False)`, I got a walkthrough of *why*
  bidirectional dataclasses recurse in `__eq__`/`__repr__`. I learned the "why,"
  not just a fix to paste.
- **Diagram generation from a rough sketch.** Turning my attribute/method notes
  into a mermaid class diagram gave me a clean visual to react to at design time.

*One AI suggestion I rejected or modified to keep the design clean:*

For recurring tasks I specified that a completed daily task's next due date should
be "today + 1 day." The assistant implemented that but suggested an alternative
that bases the next date on the task's own `due_date`, so a task completed days
late would keep its original cadence. I **rejected the extra behavior**: it wasn't
a requirement and would have introduced date-math edge cases I'd have to justify
and test. Keeping the simple today-based rule made `mark_complete()` easy to
reason about. (Similarly, I kept `sort_by_time()` using a readable `"HH:MM"`
string key even after the assistant noted that sorting the `time` objects
directly is marginally faster — clarity mattered more than micro-optimization at
this scale.)

*How using separate chat sessions for different phases helped me stay organized:*

I kept design, implementation, debugging, and reflection in separate threads. Each
session stayed focused on one job — the design chat was about the UML and class
responsibilities, the build chat about methods, the debugging chat about the
Streamlit bug — so the assistant's context wasn't polluted with unrelated history
and its suggestions stayed on-topic. It also left me a natural per-phase record of
my decisions, which made writing this reflection far easier: I could look back at
exactly what each phase produced.

*What I learned about being the "lead architect" when collaborating with powerful AI:*

The AI is an extremely fast implementer and explainer, but it does not own the
design — I do. The clearest lesson was the Streamlit bug: the assistant wrote UI
code that looked correct and even flashed a "success" message, yet tasks silently
disappeared because Streamlit handed back a *copy* of my `Pet` object instead of
the real one. Catching it took me insisting on a real test, not trusting the
green checkmark. My takeaway: powerful tools produce confident, plausible, and
occasionally subtly-wrong code, so the architect's job is to hold the mental model
of the system (data classes *store*, the Scheduler *decides*), set the boundaries,
demand verification over trust, and reject complexity that doesn't serve the
design. The AI accelerates the work; the architectural judgment — and the
responsibility for correctness — stays with me.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
