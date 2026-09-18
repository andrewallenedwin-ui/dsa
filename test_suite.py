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

    def test_subject_queue_manager_fifo(self):
        from dsa_structures import SubjectQueueManager
        sqm = SubjectQueueManager()
        sqm.enqueue('BSC-CS-AID', {'id': 101, 'name': 'Karthik'})
        sqm.enqueue('BSC-CS-AID', {'id': 102, 'name': 'Siddharth'})
        sqm.enqueue('BCOM-AF', {'id': 103, 'name': 'Priya'})

        self.assertEqual(sqm.size('BSC-CS-AID'), 2)
        self.assertEqual(sqm.size('BCOM-AF'), 1)
        self.assertEqual(sqm.total_waiting(), 3)

        first_cs = sqm.dequeue('BSC-CS-AID')
        self.assertEqual(first_cs['name'], 'Karthik')
        self.assertEqual(sqm.size('BSC-CS-AID'), 1)

    def test_six_marks_application_and_percentage(self):
        import uuid
        payload = {
            'name': 'Gautam Natarajan',
            'email': f'gautam.{uuid.uuid4().hex[:8]}@example.com',
            'phone': '9840123987',
            'department': 'B.Sc Computer Science',
            'stream': 'Aided',
            'm1': 95.0,
            'm2': 90.0,
            'm3': 92.0,
            'm4': 98.0,
            'm5': 94.0,
            'm6': 91.0,
            'gender': 'Male'
        }
        res = self.app.post('/api/apply', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['marks_total'], 560.0)
        self.assertAlmostEqual(data['marks'], 93.33, places=1)
        self.assertEqual(data['course_code'], 'BSC-CS-AID')

    def test_certificate_verification(self):
        students = models.get_all_students()
        self.assertGreater(len(students), 0)
        target_id = students[0]['id']

        res = self.app.post(f'/api/student/{target_id}/verify-cert', data=json.dumps({
            'status': 'verified',
            'remarks': 'SSLC, HSC, TC, Community approved'
        }), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['cert_status'], 'verified')

    def test_database_has_1000_plus_students(self):
        all_s = models.get_all_students()
        self.assertGreaterEqual(len(all_s), 1000)

    def test_rejection_tracking_and_reasons(self):
        res = self.app.get('/api/dashboard')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('total_rejected', data)
        self.assertGreater(data['total_rejected'], 0)
        self.assertIn('rejection_marks_count', data)
        self.assertIn('rejection_cert_count', data)
        self.assertIn('rejection_fees_count', data)
        self.assertGreater(data['rejection_marks_count'], 0)
        self.assertGreater(data['rejection_cert_count'], 0)
        self.assertGreater(data['rejection_fees_count'], 0)

        # Test /api/rejections endpoint
        rej_res = self.app.get('/api/rejections')
        self.assertEqual(rej_res.status_code, 200)
        rej_data = rej_res.get_json()
        self.assertTrue(rej_data['success'])
        self.assertEqual(rej_data['total_rejected'], data['total_rejected'])
        self.assertGreater(len(rej_data['students']), 0)
        first_rej = rej_data['students'][0]
        self.assertTrue(len(first_rej.get('rejection_reason', '')) > 0)

    def test_reject_student_with_reason_and_undo(self):
        # 1. Submit application
        import uuid
        payload = {
            'name': 'Test Rejection Applicant',
            'email': f'test.reject.{uuid.uuid4().hex[:8]}@example.com',
            'phone': '9342311026',
            'department': 'B.Sc Mathematics',
            'stream': 'Aided',
            'marks': 55.0,
            'gender': 'Female'
        }
        res = self.app.post('/api/apply', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        s_id = res.get_json()['student_id']

        # 2. Reject with reason
        reason_text = "Marks Below Cutoff: HSC aggregate did not meet cutoff of 75.0%"
        rej_res = self.app.post(f'/api/reject/{s_id}', data=json.dumps({'reason': reason_text}), content_type='application/json')
        self.assertEqual(rej_res.status_code, 200)
        self.assertTrue(rej_res.get_json()['success'])
        self.assertEqual(rej_res.get_json()['rejection_reason'], reason_text)

        # 3. Check status reflects rejection and reason
        status_res = self.app.get(f'/api/student/{s_id}')
        self.assertEqual(status_res.status_code, 200)
        self.assertEqual(status_res.get_json()['student']['status'], 'rejected')
        self.assertEqual(status_res.get_json()['student']['rejection_reason'], reason_text)

        # 4. Undo rejection via Stack LIFO
        undo_res = self.app.post('/api/undo')
        self.assertEqual(undo_res.status_code, 200)
        self.assertTrue(undo_res.get_json()['success'])

        # 5. Check restored to pending
        status_res2 = self.app.get(f'/api/student/{s_id}')
        self.assertEqual(status_res2.get_json()['student']['status'], 'pending')

    def test_course_tuition_fees(self):
        res = self.app.get('/api/courses')
        self.assertEqual(res.status_code, 200)
        courses = res.get_json()['courses']
        for c in courses:
            self.assertIn('tuition_fee', c)
            self.assertGreater(c['tuition_fee'], 0)
        
        # Check Aided fee vs SFS fee realistic ranges
        aided_fees = [c['tuition_fee'] for c in courses if c['stream'] == 'Aided']
        sfs_fees = [c['tuition_fee'] for c in courses if c['stream'] == 'SFS']
        self.assertGreater(min(sfs_fees), max(aided_fees))

    def test_abc_friend_chat_bilingual(self):
        # 1. English Fee Query
        res1 = self.app.post('/api/chat', data=json.dumps({
            'message': 'What is the fee for B.Sc Computer Science?',
            'lang': 'en'
        }), content_type='application/json')
        self.assertEqual(res1.status_code, 200)
        d1 = res1.get_json()
        self.assertTrue(d1['success'])
        self.assertIn('B.Sc Computer Science', d1['reply'])
        self.assertIn('₹', d1['reply'])

        # 2. English Contact / Helpline Query
        res2 = self.app.post('/api/chat', data=json.dumps({
            'message': 'admission phone number',
            'lang': 'en'
        }), content_type='application/json')
        self.assertEqual(res2.status_code, 200)
        d2 = res2.get_json()
        self.assertIn('9342311026', d2['reply'])

        # 3. English DSA Query
        res3 = self.app.post('/api/chat', data=json.dumps({
            'message': 'how does the queue and selection sort work in admission?',
            'lang': 'en'
        }), content_type='application/json')
        self.assertEqual(res3.status_code, 200)
        d3 = res3.get_json()
        self.assertIn('Queue', d3['reply'])
        self.assertIn('Selection Sort', d3['reply'])

        # 4. Tamil Greeting & Query
        res4 = self.app.post('/api/chat', data=json.dumps({
            'message': 'வணக்கம், சேர்க்கை கட்டணம் என்ன?',
            'lang': 'auto'
        }), content_type='application/json')
        self.assertEqual(res4.status_code, 200)
        d4 = res4.get_json()
        self.assertTrue(d4['success'])
        self.assertEqual(d4['lang'], 'ta')
        self.assertIn('9342311026', d4['reply'])
        self.assertIn('ஏபிசி', d4['reply'])

if __name__ == '__main__':
    unittest.main()
