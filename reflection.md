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

Task:
    -id
    -description
    -scheduled_time
    -frequency (Frequency enum)
    -priority (Priority enum)
    -completed
    -pet

    mark_complete()
    reset()
    is_pending()

Pet:
    -id
    -name
    -species
    -breed
    -owner
    -tasks: list of Task

    add_task()
    remove_task()
    pending_tasks()
    completed_tasks()

Owner:
    -id
    -first name
    -last name
    -pets: list of Pet

    add_pet()
    get_pet()
    all_tasks()

Scheduler:
    -owner

    build_daily_plan()
    next_task()
    pending_tasks()
    complete_task()
    reset_daily_tasks()
    explain_plan()

I settled on four classes, each with one clear responsibility. Crucially, I
split *storing* tasks from *organizing* them — the data classes (Task, Pet,
Owner) just hold state, and a dedicated Scheduler owns all the decision-making.

- **Task** — represents a single care activity (e.g. an 8am walk). It holds the
  data needed to reason about it: `description`, `scheduled_time`, `frequency`
  (how often it repeats), `priority`, and whether it's `completed`, plus a
  back-reference to the Pet it belongs to. Its responsibility is to own its own
  state transitions — `mark_complete()`, `reset()` (re-opens a recurring task
  for its next cycle), and `is_pending()` — so nothing else has to poke at its
  fields directly.

- **Pet** — stores a pet's details (name, species, breed) and the list of Tasks
  it needs. Its responsibility is to be the home for those tasks: `add_task()`
  and `remove_task()` keep the pet ↔ task link consistent, and
  `pending_tasks()`/`completed_tasks()` give quick views of its own workload.

- **Owner** — represents the person using the app and manages multiple pets. It
  holds identity info and the list of pets, and its responsibility is
  management and aggregation: `add_pet()`, `get_pet()` to look one up, and
  `all_tasks()` to flatten every task across every pet into one list.

- **Scheduler** — the "brain" of the system. It takes an Owner and its job is
  to retrieve, organize, and prioritize tasks across all of that owner's pets:
  `build_daily_plan()` sorts pending tasks (most urgent first, then earliest
  time), `next_task()` returns the single top task, `explain_plan()` produces a
  readable ordered plan, and `reset_daily_tasks()` re-opens recurring tasks for
  a new day. It deliberately holds no task state of its own — it always reads
  live from the Owner — so it can never fall out of date.

I also added two small enums as supporting types: **Priority** (LOW/MEDIUM/HIGH,
built on `IntEnum` so tasks sort by urgency directly) and **Frequency**
(ONCE/DAILY/WEEKLY/MONTHLY), which replace loose strings with a typo-safe source
of truth.

The core relationships are one-to-many: an Owner has many Pets, and a Pet has
many Tasks. I kept these links bidirectional (a Pet knows its Owner, a Task
knows its Pet) so the Scheduler can walk the object graph in either direction
when building a plan.

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
