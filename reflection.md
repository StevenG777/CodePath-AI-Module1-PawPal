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
