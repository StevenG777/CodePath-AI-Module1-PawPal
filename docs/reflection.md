# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
    We have 4 different classes (Owner, Pet, Task, Scheduler). Owner manage personal info and add their pet to the system; Pet manage pet info; Task manage task duration and priority corresponding to specific pet; Scheduler combine all tasks that belong to one pet into a plan to be view by Owner.
    
- What classes did you include, and what responsibilities did you assign to each?
    - Owner class
        - Attributes: 
            - owner name (string) 
            - pet names (list of string) 
        - Methods:
            - add user info
            - edit user info
            - delete user info
            - add pet under this user
    - Pet class
        - Attributes:
            - name (string)
            - owner name (string)
        - Methods:
            - add pet info
            - edit pet info
            - delete pet info
    - Task class
        - Attributes:
            - task name (string)
            - pet name (string)
            - duration (int)
            - priority (category string)
        - Methods:
            - add task
            - add duration and priority
            - edit task
            - delete task
            - display task for certain day
    - Scheduler
        - Attributes:
            - task names (list of string)
            - durations (list of durations)
            - priorities (list of priority)
            - pet name (string)
        - Methods:
            - generate schedules
            - display schedules

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
YES
- Wrong Relationship
    - Owner and Task should hold Pet object instead of Pet name, to avoid name lookup
    - Pet has no way to look up its corresponding task while task can reference back to Pet; Pet can only do that through Scheduler. By adding task related attribute on Pet can help bypass intermediate access to Scheduler class
- Wrong Logic
    - Task.display_for_day() should be a Scheduler function
    - Task.delete_task is wrong, you cannot delete an object from itself
    - Scheduler does not have constraint attributes to fulfill the requirement of consider "time available"
    - Owner.add_info() is redundant from Owner.__init__() just like previous Pet design
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
The scheduler considers three constraints: 
    1. available time (available_minutes)
    2. task priority (high/medium/low)
    3. recurrence readiness (whether enough time has elapsed for a weekly or daily task to be due again)

- How did you decide which constraints mattered most?
Decisions:
    1. Time was made the primary constraint because it's the most objective. i.e. you can't create more minutes in a day. 
    2. Priority was second because not all pet care tasks are equally urgent. i.e. a flea treatment can wait; a feeding can't. 
    3. Recurrence was last because it's a correctness concern, not a preference. i.e.a weekly grooming that was done yesterday shouldn't appear today regardless of priority.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
The scheduler uses a greedy algorithm: it picks tasks in priority order and adds each one if it fits, skipping it permanently if it doesn't, for which it never backtracks to try a different combination.

- Why is that tradeoff reasonable for this scenario?
This is more efficient in handling tasks in large scale

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?
I used AI in all stage of the implementation, including design brainstorming, test case generation, debuggin, refactoring, OOP implementation, algorithm analysis. THe question where it includes details about edge cases and analysis of what could went wrong on algorithm analysis

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?
There is a moment where I asked less than I should, so I need to re-prompt it for AI and 

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?
I tested all the core smart functions:
    - Sorting Correctness
    - Recurrence Logic
    - Conflict Detection
    - Schedule Generation Edge Cases
They are important because they are proof that the app is reliable in performing these functions

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?
Sorting Correctness
I am 10/10 confident, I could not think of any edge case so far to test next.git add .

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
I am most satified with the passed testing of unit testing

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
I will have functionalities to edit personal and pet information

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
System Design is iterative in long term, but it's important to think through regarding the data flow, edge case and all aspect of system. It will be costly to re-architect the system