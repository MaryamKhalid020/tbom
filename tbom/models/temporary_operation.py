from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TemporaryOperation(models.Model):
    _name = 'tbom.temporary.operation'
    _description = 'Temporary Business Operation'
    _order = 'start_date desc'

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The Operation Code must be unique.'),
    ]

    name = fields.Char(
        string='Operation Name',
        required=True
    )

    code = fields.Char(
        string='Operation Code',
        required=True
    )

    operation_type = fields.Selection(
        [
            ('exhibition', 'Exhibition'),
            ('trade_fair', 'Trade Fair'),
            ('seasonal_outlet', 'Seasonal Outlet'),
            ('promotional_campaign', 'Promotional Campaign'),
            ('temporary_warehouse', 'Temporary Warehouse'),
            ('field_operation', 'Field Operation'),
            ('other', 'Other'),
        ],
        string='Operation Type',
        required=True
    )

    location = fields.Char(
        string='Location',
        required=True
    )

    start_date = fields.Date(
        string='Start Date',
        required=True
    )

    end_date = fields.Date(
        string='End Date',
        required=True
    )

    description = fields.Text(
        string='Description'
    )

    state = fields.Selection(
        [
            ('planned', 'Planned'),
            ('setup', 'Setup'),
            ('active', 'Active'),
            ('closing', 'Closing'),
            ('closed', 'Closed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='planned',
        required=True
    )

    responsible_id = fields.Many2one(
        'res.users',
        string='Responsible Manager'
    )

    budget = fields.Float(
        string='Budget'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    employee_ids = fields.Many2many(
        'hr.employee',
        string='Assigned Employees'
    )

    resource_ids = fields.One2many(
        'tbom.resource',
        'operation_id',
        string='Resources'
    )

    # Validations
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date:
                if record.end_date < record.start_date:
                    raise ValidationError(
                        'End Date cannot be earlier than Start Date.'
                    )

    @api.constrains('budget')
    def _check_budget(self):
        for record in self:
            if record.budget < 0:
                raise ValidationError(
                    'Budget cannot be negative.'
                )

    # Workflow Actions
    def action_setup(self):
        for record in self:
            if record.state != 'planned':
                raise ValidationError('Start Setup is only allowed in Planned state.')
            record.state = 'setup'

    def action_activate(self):
        for record in self:
            if record.state != 'setup':
                raise ValidationError('Activate is only allowed in Setup state.')
            record.state = 'active'

    def action_closing(self):
        for record in self:
            if record.state != 'active':
                raise ValidationError('Start Closing is only allowed in Active state.')
            record.state = 'closing'

    def action_close(self):
        for record in self:
            if record.state != 'closing':
                raise ValidationError('Close Operation is only allowed in Closing state.')
            record.state = 'closed'

    def action_cancel(self):
        for record in self:
            if record.state in ('closed', 'cancelled'):
                raise ValidationError('Cannot cancel an operation that is already closed or cancelled.')
            record.state = 'cancelled'

    def action_draft(self):
        for record in self:
            if record.state != 'cancelled':
                raise ValidationError('Reset to Planned is only allowed for Cancelled operations.')
            record.state = 'planned'