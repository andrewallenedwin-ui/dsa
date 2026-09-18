# ABC College of Arts & Science — Online Admission System
> **Data Structures & Algorithms (DSA) ICA 2 Project**  
> **Author:** Allen Paul  
> **Problem Statement:** Transform a manual, paper-based offline college admission process into an automated, transparent online web application leveraging core DSA concepts with visual demonstration.

---

## 📌 Problem & Real-World Motivation

In traditional offline college admissions at **ABC Arts & Science College**:
- Students stand in long physical queues for hours without knowing when their token will be called.
- College administrators manage applications with physical registers, causing errors and making it nearly impossible to undo accidental allocations.
- Calculating department merit cutoffs manually is slow, error-prone, and lacks transparency.

**Our Solution:** A full-stack web application that models real-world admissions using **Queue (FIFO)**, **Stack (LIFO)**, and **Selection Sort**, paired with a **Real-Time Master Board** for dynamic seat filling monitoring.

---

## 🧠 DSA Concepts Implemented & Analyzed

### 1. Queue Data Structure (FIFO — First In, First Out)
- **Role in Application:** Manages applicant intake in the exact order applications are submitted.
- **Operations:**
  - `enqueue(student)`: Inserts a newly submitted application to the tail (rear) of the queue.
  - `dequeue()`: Extracts and processes the applicant at the head (front) of the queue to allocate a college seat.
  - `peek()`: Inspects the front of the queue without removing the student.
- **Time Complexity:** $\mathcal{O}(1)$ for all queue operations using double-ended queue (`collections.deque`).

---

### 2. Stack Data Structure (LIFO — Last In, First Out)
- **Role in Application:** Powers the admission officer's **Undo / Rollback Desk**.
- **Operations:**
  - `push(action)`: Pushes every admission or rejection decision onto the top of the stack.
  - `pop()`: Undoes the most recent decision, reversing the database state and returning the candidate to the front of the queue.
  - `peek()`: Inspects the most recent decision on top of the stack.
- **Time Complexity:** $\mathcal{O}(1)$ push and pop operations.

---

### 3. Selection Sort Algorithm (Merit Ranking Engine)
- **Role in Application:** Automatically sorts and ranks applicants based on their **12th Standard Board Marks (%)** to generate course-wise merit cutoffs.
- **Why Selection Sort?**
  - Mimics manual evaluation: in each pass $i$, it identifies the candidate with the highest marks in the remaining unsorted applicants and places them at Rank $i$.
  - Requires minimal memory write operations ($\mathcal{O}(n)$ swaps).
- **Complexity Analysis:**
  - **Best Case:** $\mathcal{O}(n^2)$
  - **Average Case:** $\mathcal{O}(n^2)$
  - **Worst Case:** $\mathcal{O}(n^2)$
  - **Auxiliary Space:** $\mathcal{O}(1)$ (In-place sort)
- **Visualizer Feature:** The dashboard includes an interactive step-by-step trace mode displaying pass numbers, comparisons, highlighted maximum elements, and animated swaps!

---

## 📊 Master Board & Arts & Science Courses

### Supported Programs & Seat Capacities:
1. **B.Sc Computer Science** (60 Seats | Cutoff: 75%)
2. **B.Com Accounting & Finance** (80 Seats | Cutoff: 70%)
3. **B.Sc Mathematics** (50 Seats | Cutoff: 65%)
4. **B.A English Literature** (50 Seats | Cutoff: 60%)
5. **B.B.A (Business Administration)** (60 Seats | Cutoff: 68%)
6. **B.Sc Physics** (40 Seats | Cutoff: 65%)
- **Total College Capacity:** 340 Seats

### Real-Time Monitoring:
- **Seat Filling Status Per Hour:** Dynamic vertical bar chart grouping admissions by time of day (09:00 to 17:00).
- **Department Quotas:** Live progress bars showing filled vs. available seats per course.

---

## 🚀 How to Run Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python app.py
```
*(Or run `python main.py`)*

### 3. Open in Browser
- **Student Portal:** [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **Master Admin Dashboard:** [http://127.0.0.1:5000/admin](http://127.0.0.1:5000/admin)

### 4. Run Automated Tests
```bash
python test_suite.py
```

---

## 🎙️ Viva & Project Demo Guide for ICA 2

1. **Step 1: Student Application (Queue Enqueue)**
   - Go to [http://127.0.0.1:5000/](http://127.0.0.1:5000/).
   - Fill out an application form for an Arts & Science course (e.g., B.Sc Computer Science with 95%).
   - Notice the generated **Application ID** and **Queue Position**.
   - Test the **Application Status Tracker** using the ID to see the visual 4-step progress bar.

2. **Step 2: Admission Processing & Undo Desk (Queue Dequeue & Stack Pop)**
   - Switch to the [Admin Dashboard](http://127.0.0.1:5000/admin).
   - Observe the **Admission Queue (FIFO)** conveyor showing students in submission order.
   - Click **"Admit Next Student — dequeue()"**; notice the student moves out of the queue and is allocated a seat.
   - Look at the **Admin Action Stack (LIFO)**; the admission is pushed to the top plate of the stack.
   - Click **"Undo Last Action — pop()"**; the admission is reversed and the student is re-enqueued at the front of the queue!

3. **Step 3: Selection Sort Merit Evaluation**
   - Scroll to the **Selection Sort: Merit Ranking Engine** panel.
   - Select a department filter or "All Departments".
   - Click **"▶ Run Step-by-Step Animation"**.
   - Watch the bars animate pass-by-pass showing comparisons, the selected maximum candidate, and the rank-by-rank swap until the full merit list is constructed!

4. **Step 4: Master Board Hourly Monitoring**
   - Show the examiner the **Seat Filling Status Per Hour** chart and the **Department-Wise Quota Progress Bars**, proving that the college can monitor admission inflow throughout the day.