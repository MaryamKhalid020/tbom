from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TemporaryOperation(models.Model):
    _name = 'tbom.temporary.operation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Temporary Business Operation'
    _order = 'start_date desc'

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The Operation Code must be unique.'),
    ]

    @api.model
    def _default_code(self):
        # Generate a unique code like OP-YYYY-XXXX
        today = fields.Date.today()
        year = today.year
        # Find the last code for the current year
        last_op = self.search([('code', 'like', f'OP-{year}-%')], order='code desc', limit=1)
        if last_op:
            try:
                # extract sequence number
                seq = int(last_op.code.split('-')[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        
        # Ensure it is unique
        while True:
            code = f"OP-{year}-{seq:04d}"
            if self.search_count([('code', '=', code)]) == 0:
                return code
            seq += 1

    name = fields.Char(
        string='Operation Name',
        required=True,
        tracking=True
    )

    code = fields.Char(
        string='Operation Code',
        required=True,
        tracking=True,
        default=_default_code
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
        required=True,
        tracking=True
    )

    location = fields.Char(
        string='Location',
        required=True,
        tracking=True
    )

    start_date = fields.Date(
        string='Start Date',
        required=True,
        tracking=True
    )

    end_date = fields.Date(
        string='End Date',
        required=True,
        tracking=True
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
        required=True,
        tracking=True
    )

    responsible_id = fields.Many2one(
        'res.users',
        string='Responsible Manager',
        tracking=True,
        domain=lambda self: [('groups_id', 'in', self.env.ref('tbom.group_tbom_manager').ids)]
    )

    budget = fields.Float(
        string='Budget',
        tracking=True
    )

    state_history_ids = fields.One2many(
        'tbom.operation.state.history',
        'operation_id',
        string='State History',
        readonly=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    employee_ids = fields.One2many(
        'tbom.employee.assignment',
        'operation_id',
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
        compute='_compute_dashboard_stats',
        store=True
    )

    resource_count = fields.Integer(
        string='Total Resources',
        compute='_compute_dashboard_stats',
        store=True
    )

    planned_resource_count = fields.Integer(
        string='Planned Resources',
        compute='_compute_dashboard_stats',
        store=True
    )

    deployed_resource_count = fields.Integer(
        string='Deployed Resources',
        compute='_compute_dashboard_stats',
        store=True
    )

    returned_resource_count = fields.Integer(
        string='Returned Resources',
        compute='_compute_dashboard_stats',
        store=True
    )

    total_expenses = fields.Float(
        string='Total Expenses',
        compute='_compute_dashboard_stats',
        store=True,
        help="Sum of all recorded expense amounts for this operation."
    )

    remaining_budget = fields.Float(
        string='Remaining Budget',
        compute='_compute_dashboard_stats',
        store=True,
        help="Calculated as allocated Budget minus Total Expenses."
    )

    budget_utilization = fields.Float(
        string='Budget Utilization (%)',
        compute='_compute_dashboard_stats',
        store=True,
        help="Percentage of Budget spent, calculated as (Total Expenses / Budget) * 100."
    )

    duration = fields.Integer(
        string='Total Duration (Days)',
        compute='_compute_operation_duration',
        store=True,
        help="Total days between Start Date and End Date inclusive."
    )
    days_elapsed = fields.Integer(
        string='Days Elapsed',
        compute='_compute_operation_duration',
        store=True,
        help="Days passed since Start Date up to Today."
    )
    days_remaining = fields.Integer(
        string='Days Remaining',
        compute='_compute_operation_duration',
        store=True,
        help="Days remaining until End Date."
    )
    equipment_count = fields.Integer(
        string='Equipment Count',
        compute='_compute_operation_counts',
        store=True
    )
    deployed_equipment_count = fields.Integer(
        string='Deployed Equipment Count',
        compute='_compute_operation_counts',
        store=True
    )
    expense_count = fields.Integer(
        string='Expense Count',
        compute='_compute_operation_counts',
        store=True
    )
    state_history_count = fields.Integer(
        string='State History Count',
        compute='_compute_operation_counts',
        store=True
    )

    is_over_budget = fields.Boolean(
        string='Over Budget',
        compute='_compute_risk_indicators',
        store=True,
        help="True when Total Expenses exceed the allocated Budget."
    )
    is_near_budget = fields.Boolean(
        string='Near Budget Limit',
        compute='_compute_risk_indicators',
        store=True,
        help="True when Budget Utilization reaches 90% or higher."
    )
    is_ending_soon = fields.Boolean(
        string='Ending Soon',
        compute='_compute_risk_indicators',
        store=True,
        help="True when operation is active and end date is within 3 days."
    )
    is_overdue = fields.Boolean(
        string='Overdue Operation',
        compute='_compute_risk_indicators',
        store=True,
        help="True when operation remains active past its scheduled End Date."
    )
    has_outstanding_resources_closing = fields.Boolean(
        string='Outstanding Resources in Closing',
        compute='_compute_risk_indicators',
        store=True
    )
    has_outstanding_equipment_closing = fields.Boolean(
        string='Outstanding Equipment in Closing',
        compute='_compute_risk_indicators',
        store=True
    )
    missing_closing_info = fields.Boolean(
        string='Missing Closing Info',
        compute='_compute_risk_indicators',
        store=True
    )
    risk_level = fields.Selection(
        [
            ('normal', 'Normal'),
            ('warning', 'Warning'),
            ('critical', 'Critical')
        ],
        string='Operation Risk Level',
        compute='_compute_risk_indicators',
        store=True,
        help="Evaluated as Critical (Over Budget / Overdue), Warning (Near Limit / Ending Soon / Outstanding Items), or Normal."
    )

    checklist_resources_returned = fields.Boolean(
        string='All Resources Returned',
        compute='_compute_closing_checklist',
        store=True
    )
    checklist_equipment_returned = fields.Boolean(
        string='All Equipment Returned',
        compute='_compute_closing_checklist',
        store=True
    )
    checklist_expenses_recorded = fields.Boolean(
        string='Expenses Recorded',
        compute='_compute_closing_checklist',
        store=True
    )
    checklist_no_outstanding = fields.Boolean(
        string='No Outstanding Operational Items',
        compute='_compute_closing_checklist',
        store=True
    )
    checklist_dates_available = fields.Boolean(
        string='Required Dates Available',
        compute='_compute_closing_checklist',
        store=True
    )
    checklist_financials_ok = fields.Boolean(
        string='Final Financials OK',
        compute='_compute_closing_checklist',
        store=True
    )
    checklist_ready_for_close = fields.Boolean(
        string='Operation Ready for Closure',
        compute='_compute_closing_checklist',
        store=True
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

    @api.depends('start_date', 'end_date', 'state')
    def _compute_operation_duration(self):
        today = fields.Date.today()
        for record in self:
            if record.start_date and record.end_date:
                record.duration = (record.end_date - record.start_date).days + 1
                
                # days elapsed
                if today < record.start_date:
                    record.days_elapsed = 0
                elif today > record.end_date:
                    record.days_elapsed = record.duration
                else:
                    record.days_elapsed = (today - record.start_date).days + 1
                
                # days remaining
                if today > record.end_date:
                    record.days_remaining = 0
                elif today < record.start_date:
                    record.days_remaining = record.duration
                else:
                    record.days_remaining = (record.end_date - today).days
            else:
                record.duration = 0
                record.days_elapsed = 0
                record.days_remaining = 0

    @api.depends('equipment_ids', 'equipment_ids.status', 'expense_ids', 'state_history_ids')
    def _compute_operation_counts(self):
        for record in self:
            record.equipment_count = len(record.equipment_ids)
            record.deployed_equipment_count = len(record.equipment_ids.filtered(lambda e: e.status == 'deployed'))
            record.expense_count = len(record.expense_ids)
            record.state_history_count = len(record.state_history_ids)

    @api.depends('budget', 'total_expenses', 'budget_utilization', 'start_date', 'end_date', 'state', 'deployed_resource_count', 'deployed_equipment_count', 'name', 'code')
    def _compute_risk_indicators(self):
        today = fields.Date.today()
        for record in self:
            # budget risks
            record.is_over_budget = record.budget > 0 and record.budget_utilization >= 100.0
            record.is_near_budget = record.budget > 0 and 90.0 <= record.budget_utilization < 100.0
            
            # timing risks
            record.is_ending_soon = False
            if record.state in ('planned', 'setup', 'active') and record.end_date:
                days_left = (record.end_date - today).days
                record.is_ending_soon = 0 <= days_left <= 3
                
            record.is_overdue = False
            if record.state not in ('closed', 'cancelled') and record.end_date:
                record.is_overdue = today > record.end_date
                
            # closing outstanding checks
            record.has_outstanding_resources_closing = record.state == 'closing' and record.deployed_resource_count > 0
            record.has_outstanding_equipment_closing = record.state == 'closing' and record.deployed_equipment_count > 0
            
            # missing info check
            record.missing_closing_info = record.state == 'closing' and (
                not record.name or not record.code or not record.start_date or not record.end_date
            )
            
            # calculate risk level
            if record.is_over_budget or record.is_overdue or record.missing_closing_info:
                record.risk_level = 'critical'
            elif record.is_near_budget or record.is_ending_soon or record.has_outstanding_resources_closing or record.has_outstanding_equipment_closing:
                record.risk_level = 'warning'
            else:
                record.risk_level = 'normal'

    @api.depends('deployed_resource_count', 'deployed_equipment_count', 'expense_ids', 'start_date', 'end_date', 'budget', 'total_expenses')
    def _compute_closing_checklist(self):
        for record in self:
            record.checklist_resources_returned = record.deployed_resource_count == 0
            record.checklist_equipment_returned = record.deployed_equipment_count == 0
            record.checklist_expenses_recorded = len(record.expense_ids) > 0
            record.checklist_no_outstanding = record.deployed_resource_count == 0 and record.deployed_equipment_count == 0
            record.checklist_dates_available = bool(
                record.start_date and 
                record.end_date and 
                record.end_date >= record.start_date
            )
            record.checklist_financials_ok = record.budget >= 0 and record.total_expenses >= 0
            record.checklist_ready_for_close = (
                record.checklist_resources_returned and 
                record.checklist_equipment_returned and 
                record.checklist_dates_available and 
                record.checklist_financials_ok
            )

    def action_view_resources(self):
        self.ensure_one()
        action = self.env.ref('tbom.action_tbom_resource').read()[0]
        action.update({
            'domain': [('operation_id', '=', self.id)],
            'context': {'default_operation_id': self.id},
        })
        return action

    def action_view_equipment(self):
        self.ensure_one()
        action = self.env.ref('tbom.action_tbom_equipment').read()[0]
        action.update({
            'domain': [('operation_id', '=', self.id)],
            'context': {'default_operation_id': self.id},
        })
        return action

    def action_view_expenses(self):
        self.ensure_one()
        action = self.env.ref('tbom.action_tbom_expense').read()[0]
        action.update({
            'domain': [('operation_id', '=', self.id)],
            'context': {'default_operation_id': self.id},
        })
        return action

    def action_view_employees(self):
        self.ensure_one()
        action = self.env.ref('tbom.action_tbom_employee_assignment').read()[0]
        action.update({
            'domain': [('operation_id', '=', self.id)],
            'context': {'default_operation_id': self.id},
        })
        return action

    def action_view_state_history(self):
        self.ensure_one()
        action = self.env.ref('tbom.action_tbom_state_history').read()[0]
        action.update({
            'domain': [('operation_id', '=', self.id)],
            'context': {'default_operation_id': self.id, 'create': False, 'delete': False, 'edit': False},
        })
        return action

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
            if record.state in ('closed', 'cancelled'):
                locked_fields = {
                    'name', 'code', 'operation_type', 'location', 
                    'start_date', 'end_date', 'budget', 'responsible_id', 
                    'employee_ids', 'description'
                }
                if any(k in locked_fields for k in vals):
                    raise ValidationError('Closed or cancelled operations cannot be edited.')
            if 'state' in vals and vals['state'] != record.state:
                self._check_manager_role()
                old_state = record.state
                new_state = vals['state']

                # Validate transition rules
                if new_state == 'setup':
                    if old_state != 'planned':
                        raise ValidationError('Start Setup is only allowed in Planned state.')
                    
                    # Extract validation fields from vals, falling back to record values
                    name = vals.get('name', record.name)
                    code = vals.get('code', record.code)
                    responsible_id = vals.get('responsible_id', record.responsible_id.id if record.responsible_id else False)
                    operation_type = vals.get('operation_type', record.operation_type)
                    location = vals.get('location', record.location)
                    start_date = fields.Date.to_date(vals.get('start_date') or record.start_date)
                    end_date = fields.Date.to_date(vals.get('end_date') or record.end_date)
                    budget = vals.get('budget', record.budget)
                    
                    if not name or not code or not responsible_id or not operation_type or not location or not start_date or not end_date:
                        raise ValidationError("Required operation details (Name, Code, Manager, Type, Location, Start/End Dates) are missing for Setup transition.")
                    if end_date < start_date:
                        raise ValidationError("End Date cannot be earlier than Start Date.")
                    if budget < 0:
                        raise ValidationError("Budget cannot be negative.")
                elif new_state == 'active':
                    if old_state != 'setup':
                        raise ValidationError('Start Operation is only allowed in Setup state.')
                elif new_state == 'closing':
                    if old_state != 'active':
                        raise ValidationError('Start Closing is only allowed in Active state.')

                    # Create a Closing Activity
                    activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
                    activity_type_id = activity_type.id if activity_type else False
                    if not activity_type_id:
                        activity_type_id = self.env['mail.activity.type'].search([('category', '=', 'default')], limit=1).id

                    model_id = self.env['ir.model'].search([('model', '=', 'tbom.temporary.operation')], limit=1).id

                    existing_activity = self.env['mail.activity'].search([
                        ('res_id', '=', record.id),
                        ('res_model_id', '=', model_id),
                        ('summary', '=', 'Operation Closing Review Required'),
                        ('user_id', '=', record.responsible_id.id or self.env.user.id),
                    ], limit=1)

                    if not existing_activity:
                        self.env['mail.activity'].create({
                            'activity_type_id': activity_type_id,
                            'summary': 'Operation Closing Review Required',
                            'note': '<p>A closing review is required. Please check the following:</p>'
                                    '<ul>'
                                    '<li>Verify all resources have been returned</li>'
                                    '<li>Verify equipment has been returned</li>'
                                    '<li>Review outstanding expenses</li>'
                                    '<li>Review budget utilization</li>'
                                    '<li>Confirm operation dates</li>'
                                    '<li>Prepare/review final report</li>'
                                    '</ul>',
                            'res_id': record.id,
                            'res_model_id': model_id,
                            'user_id': record.responsible_id.id or self.env.user.id,
                            'date_deadline': fields.Date.context_today(self),
                        })
                elif new_state == 'closed':
                    if old_state != 'closing':
                        raise ValidationError('Close Operation is only allowed in Closing state.')
                    
                    # Extract validation fields from vals, falling back to record values
                    name = vals.get('name', record.name)
                    code = vals.get('code', record.code)
                    start_date = fields.Date.to_date(vals.get('start_date') or record.start_date)
                    end_date = fields.Date.to_date(vals.get('end_date') or record.end_date)
                    
                    if not name or not code or not start_date or not end_date:
                        raise ValidationError("Required operation details are missing.")
                    if end_date < start_date:
                        raise ValidationError("End Date cannot be earlier than Start Date.")
                    
                    outstanding_resources = record.resource_ids.filtered(lambda r: r.status == 'deployed')
                    outstanding_equipment = record.equipment_ids.filtered(lambda e: e.status == 'deployed')
                    if outstanding_resources or outstanding_equipment:
                        raise ValidationError("Operation cannot be closed because some resources or equipment are still outstanding (deployed).")
                elif new_state == 'cancelled':
                    if old_state in ('closed', 'cancelled'):
                        raise ValidationError('Cannot cancel an operation that is already closed or cancelled.')
                elif new_state == 'planned':
                    if old_state != 'cancelled':
                        raise ValidationError('Reset to Planned is only allowed for Cancelled operations.')
                else:
                    raise ValidationError('Invalid status.')

                # Create state history record
                self.env['tbom.operation.state.history'].create({
                    'operation_id': record.id,
                    'previous_state': old_state,
                    'new_state': new_state,
                    'user_id': self.env.user.id,
                })
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
            if not record.name or not record.code or not record.responsible_id or not record.operation_type or not record.location or not record.start_date or not record.end_date:
                raise ValidationError("Required operation details (Name, Code, Manager, Type, Location, Start/End Dates) are missing for Setup transition.")
            if record.end_date < record.start_date:
                raise ValidationError("End Date cannot be earlier than Start Date.")
            if record.budget < 0:
                raise ValidationError("Budget cannot be negative.")
            record.state = 'setup'
        return True

    def action_activate(self):
        self._check_manager_role()
        for record in self:
            if record.state != 'setup':
                raise ValidationError('Start Operation is only allowed in Setup state.')
            record.state = 'active'
        return True

    def action_closing(self):
        self._check_manager_role()
        for record in self:
            if record.state != 'active':
                raise ValidationError('Start Closing is only allowed in Active state.')
            record.state = 'closing'
        return True

    def action_close(self):
        self._check_manager_role()
        for record in self:
            if record.state != 'closing':
                raise ValidationError('Close Operation is only allowed in Closing state.')
            
            if not record.name or not record.code or not record.start_date or not record.end_date:
                raise ValidationError("Required operation details are missing.")
                
            if record.end_date < record.start_date:
                raise ValidationError("End Date cannot be earlier than Start Date.")
                
            outstanding_resources = record.resource_ids.filtered(lambda r: r.status == 'deployed')
            outstanding_equipment = record.equipment_ids.filtered(lambda e: e.status == 'deployed')
            
            if outstanding_resources or outstanding_equipment:
                raise ValidationError("Operation cannot be closed because some resources or equipment are still outstanding (deployed).")
                
            record.state = 'closed'
        return True

    def action_cancel(self):
        self._check_manager_role()
        for record in self:
            if record.state in ('closed', 'cancelled'):
                raise ValidationError('Cannot cancel an operation that is already closed or cancelled.')
            record.state = 'cancelled'
        return True

    def action_draft(self):
        self._check_manager_role()
        for record in self:
            if record.state != 'cancelled':
                raise ValidationError('Reset to Planned is only allowed for Cancelled operations.')
            record.state = 'planned'
        return True

    def copy(self, default=None):
        default = dict(default or {})
        
        # Suffix the code until it is unique in the database
        code = self.code or ''
        new_code = f"{code}_copy"
        while self.env['tbom.temporary.operation'].search_count([('code', '=', new_code)]) > 0:
            new_code = f"{new_code}_copy"
            
        default.update({
            'code': new_code,
            'state': 'planned',
            'expense_ids': False,
            'state_history_ids': False,
            'resource_ids': False,
            'equipment_ids': False,
        })
        copied_operation = super(TemporaryOperation, self).copy(default)
        
        # Copy resources and reset status to planned
        for resource in self.resource_ids:
            resource.copy({
                'operation_id': copied_operation.id,
                'status': 'planned',
            })
            
        # Copy equipment and reset status to planned
        for equip in self.equipment_ids:
            equip.copy({
                'operation_id': copied_operation.id,
                'status': 'planned',
                'return_date': False,
            })
            
        return copied_operation

    @api.model
    def cron_operation_reminders(self, *args, **kwargs):
        from datetime import timedelta
        today = fields.Date.today()
        # Active operations approaching end date (exactly in 3 days)
        approaching_date = today + timedelta(days=3)
        ops_approaching = self.search([
            ('state', 'in', ('setup', 'active')),
            ('end_date', '=', approaching_date),
            ('responsible_id', '!=', False)
        ])
        
        model_id = self.env['ir.model'].search([('model', '=', 'tbom.temporary.operation')], limit=1).id
        
        for op in ops_approaching:
            existing = self.env['mail.activity'].search([
                ('res_id', '=', op.id),
                ('res_model_id', '=', model_id),
                ('summary', '=', 'Operation Approaching End Date'),
            ], limit=1)
            if not existing:
                self.env['mail.activity'].create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False).id or self.env['mail.activity.type'].search([('category', '=', 'default')], limit=1).id,
                    'summary': 'Operation Approaching End Date',
                    'note': f'<p>Operation {op.name} is approaching its end date ({op.end_date}). Please review outstanding items.</p>',
                    'res_id': op.id,
                    'res_model_id': model_id,
                    'user_id': op.responsible_id.id,
                    'date_deadline': op.end_date,
                })
                
        # Overdue active operations (past end date)
        ops_overdue = self.search([
            ('state', 'in', ('setup', 'active')),
            ('end_date', '<', today),
            ('responsible_id', '!=', False)
        ])
        
        for op in ops_overdue:
            existing = self.env['mail.activity'].search([
                ('res_id', '=', op.id),
                ('res_model_id', '=', model_id),
                ('summary', '=', 'Overdue Operation Warning'),
            ], limit=1)
            if not existing:
                self.env['mail.activity'].create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False).id or self.env['mail.activity.type'].search([('category', '=', 'default')], limit=1).id,
                    'summary': 'Overdue Operation Warning',
                    'note': f'<p>Operation {op.name} is overdue! Its end date was {op.end_date} but it remains active. Please update or close it.</p>',
                    'res_id': op.id,
                    'res_model_id': model_id,
                    'user_id': op.responsible_id.id,
                    'date_deadline': today,
                })
        return True

    def action_open_send_message_wizard(self):
        self.ensure_one()
        return {
            'name': 'Send Message',
            'type': 'ir.actions.act_window',
            'res_model': 'tbom.send.message.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_operation_id': self.id,
                'default_subject': f"Notification regarding Temporary Operation: {self.name} ({self.code})",
            }
        }