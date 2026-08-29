import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import unittest
from unittest.mock import MagicMock
from app.nodes.guardrails.max_attempts import check_max_attempts
from app.nodes.guardrails.dispute_status import check_dispute_status
from app.nodes.guardrails.ptp_suppression import check_ptp_suppression

class TestGuardrails(unittest.TestCase):
    def test_max_attempts_passed(self):
        db = MagicMock()
        db.query().filter().count.return_value = 2
        event = {"id": "evt_1"}
        res = check_max_attempts(event, db)
        self.assertTrue(res["passed"])
        
    def test_max_attempts_blocked(self):
        db = MagicMock()
        db.query().filter().count.return_value = 3
        event = {"id": "evt_1"}
        res = check_max_attempts(event, db)
        self.assertFalse(res["passed"])
        self.assertEqual(res["rule_name"], "max_attempts_limit")
        
    def test_dispute_passed(self):
        db = MagicMock()
        event = {"id": "evt_1", "raw_payload": {"dispute_opened": False}}
        res = check_dispute_status(event, db)
        self.assertTrue(res["passed"])

    def test_dispute_blocked(self):
        db = MagicMock()
        event = {"id": "evt_1", "raw_payload": {"dispute_opened": True}}
        res = check_dispute_status(event, db)
        self.assertFalse(res["passed"])
        self.assertEqual(res["rule_name"], "no_active_dispute")
        
    def test_ptp_passed(self):
        db = MagicMock()
        db.query().filter().count.return_value = 0
        event = {"id": "evt_1"}
        res = check_ptp_suppression(event, db)
        self.assertTrue(res["passed"])

    def test_ptp_blocked(self):
        db = MagicMock()
        db.query().filter().count.return_value = 1
        event = {"id": "evt_1"}
        res = check_ptp_suppression(event, db)
        self.assertFalse(res["passed"])
        self.assertEqual(res["rule_name"], "ptp_suppression")

if __name__ == '__main__':
    unittest.main()
