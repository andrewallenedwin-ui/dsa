import unittest
import json
from dsa_structures import AdmissionQueue, AdminActionStack, SelectionSort
from main import app
import models

class TestDSAProject(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        models.init_db()

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_queue_fifo(self):
        q = AdmissionQueue()
        q.enqueue({'id': 1, 'name': 'First'})
        q.enqueue({'id': 2, 'name': 'Second'})
        q.enqueue({'id': 3, 'name': 'Third'})

        self.assertEqual(q.size(), 3)
        self.assertEqual(q.peek()['name'], 'First')
        self.assertEqual(q.dequeue()['name'], 'First')
        self.assertEqual(q.dequeue()['name'], 'Second')
        self.assertEqual(q.dequeue()['name'], 'Third')
        self.assertTrue(q.is_empty())

    def test_stack_lifo(self):
        s = AdminActionStack()
        s.push({'type': 'ACTION_A'})
        s.push({'type': 'ACTION_B'})
        s.push({'type': 'ACTION_C'})

        self.assertEqual(s.size(), 3)
        self.assertEqual(s.peek()['type'], 'ACTION_C')
        self.assertEqual(s.pop()['type'], 'ACTION_C')
        self.assertEqual(s.pop()['type'], 'ACTION_B')
        self.assertEqual(s.pop()['type'], 'ACTION_A')
        self.assertTrue(s.is_empty())

    def test_selection_sort(self):
        students = [
            {'name': 'A', 'marks': 75.0},
            {'name': 'B', 'marks': 92.5},
            {'name': 'C', 'marks': 60.0},
            {'name': 'D', 'marks': 88.0}
        ]
        result = SelectionSort.sort_with_trace(students, key='marks', reverse=True)
        sorted_marks = [s['marks'] for s in result['sorted_students']]
        self.assertEqual(sorted_marks, [92.5, 88.0, 75.0, 60.0])
        self.assertEqual(result['sorted_students'][0]['merit_rank'], 1)
        self.assertGreater(len(result['trace_steps']), 0)

    def test_full_admission_workflow_with_alphanumeric_id(self):
        # 1. Apply
        import uuid
        apply_payload = {
            'name': 'Pooja Sundar',
            'email': f'pooja.{uuid.uuid4().hex[:8]}@example.com',
            'phone': '9840999888',
            'department': 'B.Sc Data Science',
            'stream': 'SFS',
            'marks': 95.5,
            'gender': 'Female'
        }
        res = self.app.post('/api/apply', data=json.dumps(apply_payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        student_id = data['student_id']
        app_no = data['app_no']

        # Verify alphanumeric ID format
        self.assertTrue(app_no.startswith('ABC26-SFS-'))

        # 2. Check student status by alphanumeric ID
        res = self.app.get(f'/api/student/{app_no}')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['student']['app_no'], app_no)
        self.assertEqual(res.get_json()['student']['status'], 'pending')

        # 3. Admit Next
        res = self.app.post('/api/admit-next')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()['success'])
        seat_no = res.get_json()['seat_number']
        self.assertTrue(len(seat_no) > 0)

        # 4. Undo Last Action (Stack LIFO)
        res = self.app.post('/api/undo')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()['success'])

    def test_courses_and_streams(self):
        res = self.app.get('/api/courses')
        self.assertEqual(res.status_code, 200)
        courses = res.get_json()['courses']
        self.assertGreaterEqual(len(courses), 30)

        aided = [c for c in courses if c['stream'] == 'Aided']
        sfs = [c for c in courses if c['stream'] == 'SFS']
        self.assertGreater(len(aided), 0)
        self.assertGreater(len(sfs), 0)

if __name__ == '__main__':
    unittest.main()
