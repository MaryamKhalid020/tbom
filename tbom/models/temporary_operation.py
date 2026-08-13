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

    expense_ids = fields.One2many(
        'tbom.expense',
        'operation_id',
        string='Expenses'
    )

    equipment_ids = fields.One2many(
        'tbom.equipment',
        'operation_id',
        string='Equipment'
    )

    employee_count = fields.Integer(
        string='Employee Count',
        compute='_compute_dashboard_stats'
    )

    resource_count = fields.Integer(
        string='Total Resources',
        compute='_compute_dashboard_stats'
    )

    planned_resource_count = fields.Integer(
        string='Planned Resources',
        compute='_compute_dashboard_stats'
    )

    deployed_resource_count = fields.Integer(
        string='Deployed Resources',
        compute='_compute_dashboard_stats'
    )

    returned_resource_count = fields.Integer(
        string='Returned Resources',
        compute='_compute_dashboard_stats'
    )

    total_expenses = fields.Float(
        string='Total Expenses',
        compute='_compute_dashboard_stats'
    )

    remaining_budget = fields.Float(
        string='Remaining Budget',
        compute='_compute_dashboard_stats'
    )

    budget_utilization = fields.Float(
        string='Budget Utilization (%)',
        compute='_compute_dashboard_stats'
    )

    @api.depends('employee_ids', 'resource_ids', 'budget', 'expense_ids')
    def _compute_dashboard_stats(self):
        for record in self:
            record.employee_count = len(record.employee_ids)
            record.resource_count = len(record.resource_ids)
            record.planned_resource_count = len(record.resource_ids.filtered(lambda r: r.status == 'planned'))
            record.deployed_resource_count = len(record.resource_ids.filtered(lambda r: r.status == 'deployed'))
            record.returned_resource_count = len(record.resource_ids.filtered(lambda r: r.status == 'returned'))
            record.total_expenses = sum(record.expense_ids.mapped('amount'))
            record.remaining_budget = record.budget - record.total_expenses
            if record.budget > 0:
                record.budget_utilization = (record.total_expenses / record.budget) * 100
            else:
                record.budget_utilization = 0.0

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

    def write(self, vals):
        for record in self:
            if record.state in ('closed', 'cancelled') and not any(k in vals for k in ['state']):
                raise ValidationError('Closed or cancelled operations cannot be edited.')
        return super(TemporaryOperation, self).write(vals)

    # Workflow Actions
    def _check_manager_role(self):
        if not (self.env.su or self.env.user.has_group('tbom.group_tbom_manager')):
            raise ValidationError('Only Managers are allowed to transition operation states.')

    def action_setup(self):
        self._check_manager_role()
        for record in self:
            if record.state != 'planned':
                raise ValidationError('Start Setup is only allowed in Planned state.')
            record.state = 'setup'

    def action_activate(self):
        self._check_manager_role()
        for record in self:
            if record.state != 'setup':
                raise ValidationError('Activate is only allowed in Setup state.')
            record.state = 'active'

    def action_closing(self):
        self._check_manager_role()
        for record in self:
            if record.state != 'active':
                raise ValidationError('Start Closing is only allowed in Active state.')
            record.state = 'closing'

    def action_close(self):
        self._check_manager_role()
        for record in self:
            if record.state != 'closing':
                raise ValidationError('Close Operation is only allowed in Closing state.')
            
            outstanding_resources = record.resource_ids.filtered(lambda r: r.status == 'deployed')
            outstanding_equipment = record.equipment_ids.filtered(lambda e: e.status == 'deployed')
            
            if outstanding_resources or outstanding_equipment:
                raise ValidationError("Operation cannot be closed because some resources are still outstanding.")
                
            record.state = 'closed'

    def action_cancel(self):
        self._check_manager_role()
        for record in self:
            if record.state in ('closed', 'cancelled'):
                raise ValidationError('Cannot cancel an operation that is already closed or cancelled.')
            record.state = 'cancelled'

    def action_draft(self):
        self._check_manager_role()
        for record in self:
            if record.state != 'cancelled':
                raise ValidationError('Reset to Planned is only allowed for Cancelled operations.')
            record.state = 'planned'