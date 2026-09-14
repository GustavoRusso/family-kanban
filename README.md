# Family Kanban

Create a Kanban application. 

Centralize every backend call in one services layer, and create a mock implementation of it so the whole app runs without a real backend.


Add tests.

The application specification are:

# Family Kanban — Product Plan (V1)


## Vision

**Family Kanban** helps a family see and keep the commitments they make to each other on a shared Kanban board.




Commitment types:




- **Promise** — something a family member commits to do

- **Request** — something a family member asks another member to do

- **Responsibility** — a task a family member takes on as their own

- **Consequence** — a constructive, often time-bound follow-up that helps the family move forward together

- **Reward** — an earned privilege or enjoyable activity the family celebrates




The product makes **Kanban principles** (pull, WIP limits, visible flow) easy to practice at home, while staying practical for everyday family life. Light gamification (points) celebrates participation and keeps the experience engaging.




---




## V1 Scope




### In scope




- Family members with accounts

- Passwordless sign-in via **email + one-time code** (auto sign-up for new emails)

- Commitments with the five types above

- One responsible person per commitment

- Optional start/due dates

- Kanban flow: **Backlog → Ready → Doing → Done → Confirmed**

- Past-due date shown as an **indicator** (not a column)

- Shared family board + **My commitments** view

- Swimlanes by **commitment type**

- Per-person WIP limits with gentle, playful reminders

- Confirmation by another family member

- Required points (≥ 1), shared totals, and points history

- Cancel / restore / un-confirm rules

- Lightweight history

- Join family via **QR code**

- Roles: **Admin / Member**




### Out of V1 (future)




- Negotiation / Proposed → Negotiating → Accepted

- Recurring commitments (templates → occurrence cards)

- Shared Family Rules area

- Advanced rewards / spending points on rewards

- Achievements, streaks, and progress insights

- Waiting / Blocked states

- Comments/threads (beyond one optional note)

- Email invites / family invite codes (QR only in V1)

- Passwords, social login, and other sign-in methods

- Additional role types beyond Admin / Member

- Type-specific specialized fields/behavior beyond the shared model

- Linking follow-up commitments to earlier ones

- Auto-promoting cards to Ready by start date




---




## Domain Model




### Family




- Created by any family member

- Members join by scanning a **QR code**

- An account can belong to **multiple families**, with **one active family** at a time

- Full transparency: **every member sees every commitment**




### Member




- Every family member has their own **account**, identified by **email**

- Role: **Admin** or **Member**

- Admin powers (V1): family administration (invite/remove members, rename family, and similar)

- Commitments work the same way for every member, regardless of role

- Each member has a visible **points total**




### Commitment (V1 fields)




| Field | Required | Notes |

| --- | --- | --- |

| Title | Yes | What the family agrees will happen |

| Type | Yes | Promise / Request / Responsibility / Consequence / Reward |

| Responsible person | Yes | Exactly one family member |

| Points | Yes | Integer ≥ 1 |

| Start date | No | Informational only |

| Due date/time | No | Helps the family see timing and past-due items |

| Note | No | Optional context (“why” / free text) |




No creator/requester field in V1.




### Outcomes outside the active board




- **Cancelled** — leaves the active board; kept in history so the family can look back

- **Archived** — after Confirmed; leaves the board; kept in history




---




## Kanban Board




### Columns (V1)




```

Backlog → Ready → Doing → Done → Confirmed

```




- New commitments start in **Backlog**

- **Waiting** is deferred

- Board grouping: columns + **swimlanes by type**

- Filters: family member, type, due date, and similar

- Primary UI: shared family board

- Secondary UI: **My commitments** (a focused personal view)




### Indicators (not columns)




- **Past due** — the card stays in its current column; the indicator helps the family notice it

- Due today and similar signals may appear as indicators

- WIP above the suggested limit: a playful reminder that keeps the idea visible while the member stays free to choose




### WIP limits




- **Per-person** limits on Doing (for example, up to 2 in Doing)

- Soft limits: they guide attention and learning; members can still move cards




### Start date




- Informational only

- Ready always happens through an intentional pull (Backlog → Ready)




---




## Lifecycle & Permissions




### Create




- Any family member can create a commitment for **themselves or another member**

- New commitments land in **Backlog**




### Edit (while Backlog or Ready)




- **Any family member** can edit

- Editable fields include title, type, responsible person, dates, note, and points

- Once in **Doing / Done / Confirmed**, the commitment stays stable so the agreement remains clear

- If plans change after work has started, the responsible person **cancels** and the family creates a fresh commitment




### Points




- Required; minimum value **1**

- Any family member (including the responsible person) can assign or update points

- Points may be updated only in **Backlog** or **Ready**

- Moving **Backlog → Ready** needs points already set (≥ 1)

- After entering **Doing**, the point value stays fixed (including after an un-confirm)

- Point value is **always visible** on the card (all columns)

- The card focuses on the value itself, not on who assigned the points




### Move rules




| Transition | Who |

| --- | --- |

| Backlog → Ready | Responsible person (points already set) |

| Ready → Doing | Responsible person |

| Doing → Done | Responsible person |

| Done → Confirmed | Any other family member |

| Confirmed → Archived | Responsible person |




- Archiving is available once a commitment is Confirmed

- Confirmed cards **remain on the board** until the responsible person archives them

- After archive, the commitment joins **history**




### Confirmation




- Another family member confirms completion (the responsible person invites that shared check-in)

- A card may remain in **Done** until someone is ready to confirm

- On Confirm: **points are awarded right away** to the responsible person

- Points are awarded on confirmation whether the due date is still ahead, today, or already passed




### Un-confirm




- Any family member other than the responsible person can un-confirm

- The card returns to **Doing** so work can continue

- Awarded points return from the member’s total right away

- The point value on the card stays fixed

- The commitment can still be cancelled afterward under the usual cancel rules

- Confirming again awards the points once more




### Cancel




- The **responsible person** can cancel

- Available under the usual rules, including after a return to Doing via un-confirm

- Cancelled commitments leave the active board and appear in history with status **Cancelled**

- Cancellation is recorded as an event in the commitment’s history

- Points stay with confirmed work only; any points already awarded for this commitment return from the total




### Restore (from Cancelled)




- The **responsible person** can restore

- Always returns to **Backlog**

- Previous history (including cancellation) is preserved

- Previous **point value** is restored

- Points already earned earlier are earned again by reaching Confirmed

- Points can be updated again while in Backlog/Ready




---




## Points System (V1)




### Behavior




- Recognition of contribution — spending points on rewards comes later

- Visible to the whole family

- Awarded on **Confirmed**

- Adjusted on **un-confirm** or **cancel** when points had already been awarded




### Where totals appear




- On the main family board

- In the family/member area




### Points view (shared celebration, not a ranking)




- Each member’s total stands on its own — no ranking

- Each member has a **column**

- Top of column: **current total**

- Below: earned points **per commitment**, **newest → oldest**

- Each entry: **commitment title + confirmation date + points earned**

- Every confirmed commitment awards at least 1 point




---




## History (V1)




Lightweight history entries include:




- Commitment title

- Type

- Responsible person

- Completion date (for confirmed/archived) or the matching outcome date

- Cancelled commitments appear with status **Cancelled**




---




## Authentication (V1)




Passwordless sign-in with email and a one-time code. No passwords.




### Sign-in flow




1. The user enters their **email address**

2. The app sends a **one-time code** to that email

3. The user enters the received code

4. If the code is valid, sign-in completes




### Sign-up




- There is no separate sign-up step

- If the email is **not yet registered**, the system **creates the account automatically** on successful code verification

- If the email is already registered, the same flow signs the user in to their existing account




### Notes




- Email is the account identity

- Joining a family (via QR) is separate from creating/signing into an account: first authenticate, then create or join a family




---




## Onboarding (V1)




1. A person signs in with email + one-time code (new emails auto-create an account)

2. That person creates a family (or joins one by scanning a QR code)

3. Other members sign in the same way, then join by scanning the family’s QR code

4. The family starts creating commitments on the shared board




---




## Clarifications Applied (chat incongruences)




| Topic | Resolution |

| --- | --- |

| Confirmed leaves board immediately (Q44) vs stays until archived (Q60) | **Q60** — stays until the responsible person archives |

| Creator removed (Q41) vs edit permissions unclear | **Any family member** can edit in Backlog/Ready |

| Points optional (Q49) vs assignment rules | Points are **required**, ≥ 1 |

| Responsible cannot set points (Q52) | **Any family member** can set points |

| Ready blocked until non-responsible assigns points (Q53) | Ready needs points **set** (by any member) |

| Start date controls Ready (Q4) vs manual Ready (Q10) | Start date is **informational only** |

| Change responsible person while editable? | **Yes**, any member can reassign in Backlog/Ready |

| 0-point history (Q93/Q94) | Every commitment uses points ≥ 1 |




---




## Design Principles (product)




1. Commitments are shared agreements among family members

2. The responsible person steers their own flow; another member confirms completion

3. Kanban highlights pull and WIP in a supportive, learning-friendly way

4. Past-due dates and WIP reminders are helpful signals on the board, not separate workflows

5. Points celebrate participation; they highlight each member’s progress, not a competition

6. The family board is open and transparent by default

7. V1 stays focused: strong commitment and board mechanics first, richer celebration features later

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/bb2058ca-40a1-4c79-bf7b-738693d5d681).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
