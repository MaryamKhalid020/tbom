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

    def test_date_validation_same_date(self):
        """Test that start date and end date being the same is valid."""
        op = self.operation_model.create({
            'name': 'Exhibition Same Date',
            'code': 'OP-2026-DATE-SAME',
            'operation_type': 'exhibition',
            'location': 'Hall 1',
            'start_date': '2026-09-01',
            'end_date': '2026-09-01',
        })
        self.assertEqual(op.end_date.strftime('%Y-%m-%d'), '2026-09-01')

    def test_date_validation_later_date(self):
        """Test that end date being later than start date is valid."""
        op = self.operation_model.create({
            'name': 'Exhibition Later Date',
            'code': 'OP-2026-DATE-LATER',
            'operation_type': 'exhibition',
            'location': 'Hall 1',
            'start_date': '2026-09-01',
            'end_date': '2026-09-02',
        })
        self.assertEqual(op.end_date.strftime('%Y-%m-%d'), '2026-09-02')

    def test_date_validation_invalid_date(self):
        """Test that an earlier end date raises a ValidationError."""
        with self.assertRaises(ValidationError):
            self.operation_model.create({
                'name': 'Exhibition Invalid Date',
                'code': 'OP-2026-DATE-INVALID',
                'operation_type': 'exhibition',
                'location': 'Hall 1',
                'start_date': '2026-09-02',
                'end_date': '2026-09-01',
            })

    def test_dashboard_computed_fields(self):
        """Test that the operation dashboard computed fields calculate values correctly."""
        op = self.operation_model.create({
            'name': 'Exhibition Dashboard',
            'code': 'OP-2026-DASHBOARD',
            'operation_type': 'exhibition',
            'location': 'Hall 1',
            'start_date': '2026-09-01',
            'end_date': '2026-09-15',
            'budget': 10000.0,
        })
        # Initial checks
        self.assertEqual(op.employee_count, 0)
        self.assertEqual(op.resource_count, 0)
        self.assertEqual(op.planned_resource_count, 0)
        self.assertEqual(op.deployed_resource_count, 0)
        self.assertEqual(op.returned_resource_count, 0)
        self.assertEqual(op.total_expenses, 0.0)
        self.assertEqual(op.remaining_budget, 10000.0)

        # Add an employee
        employee = self.env['hr.employee'].create({'name': 'Test Employee'})
        op.write({'employee_ids': [(4, employee.id)]})
        self.assertEqual(op.employee_count, 1)

        # Add resources
        self.env['tbom.resource'].create({
            'name': 'Laptop 1',
            'resource_type': 'it_equipment',
            'quantity': 1,
            'operation_id': op.id,
            'status': 'planned',
        })
        self.env['tbom.resource'].create({
            'name': 'Vehicle 1',
            'resource_type': 'vehicle',
            'quantity': 1,
            'operation_id': op.id,
            'status': 'deployed',
        })
        self.env['tbom.resource'].create({
            'name': 'Table 1',
            'resource_type': 'furniture',
            'quantity': 2,
            'operation_id': op.id,
            'status': 'returned',
        })
        
        # Trigger compute
        op._compute_dashboard_stats()
        self.assertEqual(op.resource_count, 3)
        self.assertEqual(op.planned_resource_count, 1)
        self.assertEqual(op.deployed_resource_count, 1)
        self.assertEqual(op.returned_resource_count, 1)
        self.assertEqual(op.remaining_budget, 10000.0)

    def test_expense_tracking(self):
        """Test expense creation, negative rejection, and dynamic dashboard calculations."""
        op = self.operation_model.create({
            'name': 'Exhibition Expenses',
            'code': 'OP-2026-EXP',
            'operation_type': 'exhibition',
            'location': 'Hall 1',
            'start_date': '2026-09-01',
            'end_date': '2026-09-15',
            'budget': 5000.0,
        })
        self.assertEqual(op.total_expenses, 0.0)
        self.assertEqual(op.remaining_budget, 5000.0)

        # Create positive expense
        self.env['tbom.expense'].create({
            'operation_id': op.id,
            'description': 'Banner printing',
            'amount': 350.0,
            'date': '2026-09-02',
        })
        op._compute_dashboard_stats()
        self.assertEqual(op.total_expenses, 350.0)
        self.assertEqual(op.remaining_budget, 4650.0)

        # Try to create negative expense (should raise ValidationError)
        with self.assertRaises(ValidationError):
            self.env['tbom.expense'].create({
                'operation_id': op.id,
                'description': 'Refund',
                'amount': -50.0,
                'date': '2026-09-02',
            })

    def test_equipment_tracking_and_closure_validation(self):
        """Test equipment deployment tracking and operation closure validations."""
        op = self.operation_model.create({
            'name': 'Exhibition Equipment',
            'code': 'OP-2026-EQP',
            'operation_type': 'exhibition',
            'location': 'Hall 1',
            'start_date': '2026-09-01',
            'end_date': '2026-09-15',
        })
        # Create equipment (defaults to planned status)
        eqp = self.env['tbom.equipment'].create({
            'name': 'Projector A',
            'operation_id': op.id,
            'status': 'planned',
        })
        self.assertEqual(eqp.status, 'planned')

        # Deploy equipment
        eqp.write({'status': 'deployed'})
        self.assertEqual(eqp.status, 'deployed')

        # Attempt to close the operation (Planned -> Setup -> Active -> Closing -> Closed)
        op.action_setup()
        op.action_activate()
        op.action_closing()

        # Close should fail because equipment is still deployed (outstanding)
        with self.assertRaises(ValidationError):
            op.action_close()

        # Return the equipment
        eqp.write({'status': 'returned'})
        self.assertEqual(eqp.status, 'returned')

        # Close should now succeed
        op.action_close()
        self.assertEqual(op.state, 'closed')

    def test_budget_utilization_calculations(self):
        """Test budget utilization calculations including division-by-zero prevention."""
        op = self.operation_model.create({
            'name': 'Exhibition Budget',
            'code': 'OP-2026-BDG',
            'operation_type': 'exhibition',
            'location': 'Hall 1',
            'start_date': '2026-09-01',
            'end_date': '2026-09-15',
            'budget': 1000.0,
        })
        # 0 expense
        op._compute_dashboard_stats()
        self.assertEqual(op.budget_utilization, 0.0)

        # 500 expense (50% utilization)
        self.env['tbom.expense'].create({
            'operation_id': op.id,
            'description': 'Rent',
            'amount': 500.0,
            'date': '2026-09-02',
        })
        op._compute_dashboard_stats()
        self.assertEqual(op.budget_utilization, 50.0)

        # 0 budget operation
        op_zero = self.operation_model.create({
            'name': 'Zero Budget',
            'code': 'OP-2026-BDG-ZERO',
            'operation_type': 'exhibition',
            'location': 'Hall 1',
            'start_date': '2026-09-01',
            'end_date': '2026-09-15',
            'budget': 0.0,
        })
        op_zero._compute_dashboard_stats()
        self.assertEqual(op_zero.budget_utilization, 0.0)

    def test_manager_role_transitions(self):
        """Test that users without TBOM Manager group are blocked from transitioning states."""
        op = self.operation_model.create({
            'name': 'Role Test',
            'code': 'OP-2026-ROLE',
            'operation_type': 'exhibition',
            'location': 'Hall 1',
            'start_date': '2026-09-01',
            'end_date': '2026-09-15',
        })
        # Create a non-manager user
        user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'testuser',
            'email': 'testuser@example.com',
            'group_ids': [
                (6, 0, [
                    self.env.ref('base.group_user').id,
                    self.env.ref('tbom.group_tbom_user').id
                ])
            ]
        })
        
        # Call action_setup as test user -> should raise ValidationError
        with self.assertRaises(ValidationError):
            op.with_user(user).action_setup()

    def test_closed_record_write_block(self):
        """Test that closed or cancelled records block updates/edits."""
        op = self.operation_model.create({
            'name': 'Write Block Test',
            'code': 'OP-2026-WRITE',
            'operation_type': 'exhibition',
            'location': 'Hall 1',
            'start_date': '2026-09-01',
            'end_date': '2026-09-15',
        })
        op.action_setup()
        op.action_activate()
        op.action_closing()
        op.action_close()
        
        # Any write modification should raise ValidationError
        with self.assertRaises(ValidationError):
            op.write({'name': 'New Name'})

    def test_report_rendering(self):
        """Test final report generation and rendering without syntax issues."""
        op = self.operation_model.create({
            'name': 'Report Test',
            'code': 'OP-2026-REP',
            'operation_type': 'exhibition',
            'location': 'Hall 1',
            'start_date': '2026-09-01',
            'end_date': '2026-09-15',
            'budget': 2000.0,
        })
        # Render the PDF report QWeb HTML
        report = self.env['ir.actions.report']._get_report_from_name('tbom.report_temporary_operation_template')
        html_content, report_format = report._render_qweb_html([op.id])
        self.assertTrue(html_content)

    def test_employee_assignments(self):
        """Test employee assignment lifecycle, validations, and constraints."""
        op = self.operation_model.create({
            'name': 'Assignment Test',
            'code': 'OP-ASSIGN-001',
            'operation_type': 'other',
            'location': 'Test Location',
            'start_date': '2026-09-01',
            'end_date': '2026-09-15',
        })
        employee = self.env['hr.employee'].create({'name': 'Alice Job'})

        # 1. Successful assignment
        assign = self.env['tbom.employee.assignment'].create({
            'operation_id': op.id,
            'employee_id': employee.id,
            'role': 'Supervisor',
            'start_date': '2026-09-01',
            'end_date': '2026-09-10',
        })
        self.assertEqual(assign.role, 'Supervisor')
        op._compute_dashboard_stats()
        self.assertEqual(op.employee_count, 1)

        # 2. Date validation (end_date < start_date)
        with self.assertRaises(ValidationError):
            self.env['tbom.employee.assignment'].create({
                'operation_id': op.id,
                'employee_id': employee.id,
                'start_date': '2026-09-10',
                'end_date': '2026-09-01',
            })

        # 3. Duplicate Prevention validation
        with self.assertRaises(ValidationError):
            self.env['tbom.employee.assignment'].create({
                'operation_id': op.id,
                'employee_id': employee.id,
                'role': 'Duplicate Manager',
            })

        # 4. Closed operation restrictions
        op.action_setup()
        op.action_activate()
        op.action_closing()
        op.action_close()
        
        with self.assertRaises(ValidationError):
            self.env['tbom.employee.assignment'].create({
                'operation_id': op.id,
                'employee_id': self.env['hr.employee'].create({'name': 'Bob Job'}).id,
            })

    def test_send_message_wizard(self):
        """Test Send Message wizard logic, email address validation, and email creation."""
        op = self.operation_model.create({
            'name': 'Email Test',
            'code': 'OP-EMAIL-001',
            'operation_type': 'other',
            'location': 'Test Location',
            'start_date': '2026-09-01',
            'end_date': '2026-09-15',
        })

        # 1. Invalid email validation
        with self.assertRaises(ValidationError):
            self.env['tbom.send.message.wizard'].create({
                'operation_id': op.id,
                'recipient_email': 'invalid_email_format',
                'subject': 'Test Subject',
                'body': 'Test Message Body',
            })

        # 2. Valid wizard creation
        wizard = self.env['tbom.send.message.wizard'].create({
            'operation_id': op.id,
            'recipient_email': 'recipient@example.com',
            'subject': 'Test Subject',
            'body': 'Test Message Body',
        })
        self.assertEqual(wizard.recipient_email, 'recipient@example.com')

        # 3. Send message failure when no SMTP is configured
        with self.assertRaises(ValidationError):
            wizard.action_send_message()

        # 4. Send message success when SMTP server is present
        self.env['ir.mail_server'].create({
            'name': 'Test SMTP Server',
            'smtp_host': 'smtp.example.com',
            'smtp_port': 25,
            'smtp_user': 'sender@example.com',
        })
        res = wizard.action_send_message()
        self.assertEqual(res['type'], 'ir.actions.client')

        # Verify Odoo created the mail record in the native mail.mail model
        mail = self.env['mail.mail'].search([('email_to', '=', 'recipient@example.com')], limit=1)
        self.assertTrue(mail)
        self.assertEqual(mail.subject, 'Test Subject')
