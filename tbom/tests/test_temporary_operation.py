# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestTemporaryOperationLifecycle(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.operation_model = cls.env['tbom.temporary.operation']

    def test_lifecycle_success_path(self):
        """Test the standard lifecycle transition flow: Planned -> Setup -> Active -> Closing -> Closed."""
        # 1. Create - state should default to 'planned'
        op = self.operation_model.create({
            'name': 'Exhibition 2026',
            'code': 'OP-2026-099',
            'operation_type': 'exhibition',
            'location': 'Hall 1',
            'start_date': '2026-09-01',
            'end_date': '2026-09-15',
        })
        self.assertEqual(op.state, 'planned')

        # 2. Planned -> Setup
        op.action_setup()
        self.assertEqual(op.state, 'setup')

        # 3. Setup -> Active
        op.action_activate()
        self.assertEqual(op.state, 'active')

        # 4. Active -> Closing
        op.action_closing()
        self.assertEqual(op.state, 'closing')

        # 5. Closing -> Closed
        op.action_close()
        self.assertEqual(op.state, 'closed')

    def test_invalid_lifecycle_transition(self):
        """Test that skipping states or invalid transitions are blocked by ValidationError."""
        op = self.operation_model.create({
            'name': 'Exhibition 2026',
            'code': 'OP-2026-100',
            'operation_type': 'exhibition',
            'location': 'Hall 1',
            'start_date': '2026-09-01',
            'end_date': '2026-09-15',
        })
        # Cannot skip Setup (Planned -> Active should raise ValidationError)
        with self.assertRaises(ValidationError):
            op.action_activate()
        
        # State should still be planned
        self.assertEqual(op.state, 'planned')

    def test_closed_operation_cannot_be_modified_or_cancelled(self):
        """Test that once an operation is closed, it cannot transition or be cancelled."""
        op = self.operation_model.create({
            'name': 'Exhibition 2026',
            'code': 'OP-2026-101',
            'operation_type': 'exhibition',
            'location': 'Hall 1',
            'start_date': '2026-09-01',
            'end_date': '2026-09-15',
        })
        op.action_setup()
        op.action_activate()
        op.action_closing()
        op.action_close()
        
        # Cannot cancel once closed
        with self.assertRaises(ValidationError):
            op.action_cancel()
            
        # Cannot move backwards
        with self.assertRaises(ValidationError):
            op.action_setup()

    def test_cancellation_and_reset(self):
        """Test that operations can be cancelled and reset back to planned state."""
        op = self.operation_model.create({
            'name': 'Exhibition 2026',
            'code': 'OP-2026-102',
            'operation_type': 'exhibition',
            'location': 'Hall 1',
            'start_date': '2026-09-01',
            'end_date': '2026-09-15',
        })
        # Cancel from planned
        op.action_cancel()
        self.assertEqual(op.state, 'cancelled')

        # Reset to planned
        op.action_draft()
        self.assertEqual(op.state, 'planned')
