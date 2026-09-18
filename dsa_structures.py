"""
DSA Data Structures & Algorithms Module
Implements:
1. AdmissionQueue - FIFO (First In First Out) for Application Processing
2. AdminActionStack - LIFO (Last In First Out) for Decision Rollback / Undo
3. SelectionSort - O(n^2) Sorting Algorithm for Merit Ranking by 12th Board Marks
"""

from collections import deque
from datetime import datetime
import copy


class AdmissionQueue:
    """
    Queue Data Structure: FIFO (First In, First Out)
    Used to process student applications in the exact order they were submitted.
    - enqueue: Adds an applicant to the rear/tail of the queue
    - dequeue: Removes and processes the applicant at the front/head of the queue
    - peek: Inspects the applicant at the front without removal
    """

    def __init__(self):
        self.queue = deque()

    def enqueue(self, student_data):
        """Add a student to the end of the queue."""
        self.queue.append(student_data)
        return len(self.queue)

    def dequeue(self):
        """Remove and return the first student in the queue."""
        if self.queue:
            return self.queue.popleft()
        return None

    def peek(self):
        """View the student at the front of the queue without removing them."""
        if self.queue:
            return self.queue[0]
        return None

    def size(self):
        """Return the number of students waiting in the queue."""
        return len(self.queue)

    def is_empty(self):
        """Check if queue has zero items."""
        return len(self.queue) == 0

    def get_all(self):
        """Return all queue items as a standard list from head to tail."""
        return list(self.queue)

    def remove_by_id(self, student_id):
        """Remove a specific student by ID if they were rejected or canceled."""
        original_len = len(self.queue)
        self.queue = deque([s for s in self.queue if s.get("id") != student_id])
        return len(self.queue) < original_len

    def clear(self):
        self.queue.clear()


class AdminActionStack:
    """
    Stack Data Structure: LIFO (Last In, First Out)
    Used to store admission office administrative actions (Admit, Reject)
    so they can be undone in reverse chronological order.
    - push: Pushes the most recent action onto the top of the stack
    - pop: Pops and undoes the most recent action from the top of the stack
    - peek: Inspects the top action without popping
    """

    def __init__(self):
        self.stack = []

    def push(self, action_data):
        """Add latest action to the top of the stack."""
        if "timestamp" not in action_data or not action_data["timestamp"]:
            action_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.stack.append(action_data)
        return len(self.stack)

    def pop(self):
        """Remove and return the most recent action from the stack."""
        if self.stack:
            return self.stack.pop()
        return None

    def peek(self):
        """Inspect the most recent action on top of the stack."""
        if self.stack:
            return self.stack[-1]
        return None

    def size(self):
        """Return current depth of the stack."""
        return len(self.stack)

    def is_empty(self):
        """Check if stack is empty."""
        return len(self.stack) == 0

    def get_recent_actions(self, limit=10):
        """Return the most recent actions (top to bottom)."""
        return list(reversed(self.stack[-limit:]))

    def get_all(self):
        """Return entire stack (top to bottom)."""
        return list(reversed(self.stack))

    def clear(self):
        self.stack.clear()


class SelectionSort:
    """
    Selection Sort Algorithm
    Time Complexity:
      - Best Case: O(n^2)
      - Average Case: O(n^2)
      - Worst Case: O(n^2)
    Space Complexity: O(1) auxiliary (in-place)
    
    Why Selection Sort for Merit Lists?
    - Simple and deterministic.
    - Minimizes the number of write/swap operations: exactly O(n) swaps.
    - Perfectly models manual cutoff evaluation: at each pass, find the student 
      with the highest mark among the remaining pool and place them at Rank i.
    """

    @staticmethod
    def sort(students, key="marks", reverse=True):
        """
        Standard in-place Selection Sort.
        By default sorts descending (reverse=True) so highest marks appear first.
        """
        arr = list(students)
        n = len(arr)

        for i in range(n):
            target_idx = i
            for j in range(i + 1, n):
                val_j = float(arr[j].get(key, 0))
                val_target = float(arr[target_idx].get(key, 0))

                if reverse:
                    # Looking for maximum mark
                    if val_j > val_target:
                        target_idx = j
                else:
                    # Looking for minimum mark
                    if val_j < val_target:
                        target_idx = j

            # Swap elements
            if target_idx != i:
                arr[i], arr[target_idx] = arr[target_idx], arr[i]

        return arr

    @staticmethod
    def sort_with_trace(students, key="marks", reverse=True):
        """
        Selection Sort with detailed step-by-step trace generation
        for animated frontend visualization.
        """
        arr = copy.deepcopy(students)
        n = len(arr)
        trace_steps = []
        comparisons = 0
        swaps = 0

        # Initial state step
        trace_steps.append({
            "pass_num": 0,
            "description": f"Initial state before sorting. Total applicants: {n}",
            "current_index": -1,
            "compared_index": -1,
            "selected_index": -1,
            "is_swap": False,
            "array_state": copy.deepcopy(arr)
        })

        for i in range(n):
            target_idx = i
            # Step: start of pass i
            trace_steps.append({
                "pass_num": i + 1,
                "description": f"Pass {i + 1}: Finding student with highest marks starting from index {i} (Current top: {arr[target_idx].get('name', '')} with {arr[target_idx].get(key, 0)}%)",
                "current_index": i,
                "compared_index": i,
                "selected_index": target_idx,
                "is_swap": False,
                "array_state": copy.deepcopy(arr)
            })

            for j in range(i + 1, n):
                comparisons += 1
                val_j = float(arr[j].get(key, 0))
                val_target = float(arr[target_idx].get(key, 0))

                condition_met = (val_j > val_target) if reverse else (val_j < val_target)

                if condition_met:
                    old_target = target_idx
                    target_idx = j
                    trace_steps.append({
                        "pass_num": i + 1,
                        "description": f"Compared {arr[j].get('name', '')} ({val_j}%) with {arr[old_target].get('name', '')} ({val_target}%). New candidate found: {arr[j].get('name', '')} ({val_j}%)",
                        "current_index": i,
                        "compared_index": j,
                        "selected_index": target_idx,
                        "is_swap": False,
                        "array_state": copy.deepcopy(arr)
                    })

            # End of pass: perform swap if needed
            if target_idx != i:
                swaps += 1
                swapped_student_a = arr[i].get("name", "")
                swapped_student_b = arr[target_idx].get("name", "")
                arr[i], arr[target_idx] = arr[target_idx], arr[i]
                trace_steps.append({
                    "pass_num": i + 1,
                    "description": f"Pass {i + 1} Complete: Swapped Rank {i + 1} position! '{swapped_student_b}' ({arr[i].get(key, 0)}%) moved to Rank {i + 1}, '{swapped_student_a}' moved to index {target_idx}.",
                    "current_index": i,
                    "compared_index": -1,
                    "selected_index": target_idx,
                    "is_swap": True,
                    "array_state": copy.deepcopy(arr)
                })
            else:
                trace_steps.append({
                    "pass_num": i + 1,
                    "description": f"Pass {i + 1} Complete: '{arr[i].get('name', '')}' already has the highest mark ({arr[i].get(key, 0)}%) in this sub-array. No swap needed for Rank {i + 1}.",
                    "current_index": i,
                    "compared_index": -1,
                    "selected_index": i,
                    "is_swap": False,
                    "array_state": copy.deepcopy(arr)
                })

        # Add 1-based ranks to the final sorted array
        for idx, student in enumerate(arr):
            student["merit_rank"] = idx + 1

        return {
            "sorted_students": arr,
            "trace_steps": trace_steps,
            "total_comparisons": comparisons,
            "total_swaps": swaps,
            "time_complexity": "O(n²)",
            "space_complexity": "O(1) auxiliary"
        }
