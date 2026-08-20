# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class TbomEmployeeAssignment(models.Model):
    _name = 'tbom.employee.assignment'
    _description = 'Temporary Operation Employee Assignment'
    _order = 'start_date desc, id desc'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='restrict'
    )
    operation_id = fields.Many2one(
        'tbom.temporary.operation',
        string='Temporary Operation',
        required=True,
        ondelete='cascade'
    )
    job_id = fields.Many2one(
        'hr.job',
        string='Job Position',
        related='employee_id.job_id',
        store=True,
        readonly=True
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related='employee_id.department_id',
        store=True,
        readonly=True
    )
    work_phone = fields.Char(
        string='Work Phone',
        related='employee_id.work_phone',
        readonly=True
    )
    work_email = fields.Char(
        string='Work Email',
        related='employee_id.work_email',
        readonly=True
    )
    parent_id = fields.Many2one(
        'hr.employee',
        string='Manager',
        related='employee_id.parent_id',
        readonly=True
    )
    role = fields.Char(
        string='Assignment Role/Responsibility'
    )
    start_date = fields.Date(
        string='Assignment Start Date'
    )
    end_date = fields.Date(
        string='Assignment End Date'
    )
    notes = fields.Text(
        string='Notes'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.end_date < record.start_date:
                raise ValidationError("Assignment End Date cannot be earlier than Start Date.")

    @api.constrains('employee_id', 'operation_id')
    def _check_unique_assignment(self):
        for record in self:
            if record.employee_id and record.operation_id:
                duplicate = self.search([
                    ('id', '!=', record.id),
                    ('employee_id', '=', record.employee_id.id),
                    ('operation_id', '=', record.operation_id.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError("This employee is already assigned to this operation.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('operation_id'):
                operation = self.env['tbom.temporary.operation'].browse(vals['operation_id'])
                if operation.state in ('closed', 'cancelled'):
                    raise ValidationError('Cannot add employee assignments to a closed or cancelled operation.')
        return super(TbomEmployeeAssignment, self).create(vals_list)

    def write(self, vals):
        for record in self:
            if record.operation_id.state in ('closed', 'cancelled'):
                raise ValidationError('Cannot edit employee assignments of a closed or cancelled operation.')
            if 'operation_id' in vals:
                new_op = self.env['tbom.temporary.operation'].browse(vals['operation_id'])
                if new_op.state in ('closed', 'cancelled'):
                    raise ValidationError('Cannot move employee assignments to a closed or cancelled operation.')
        return super(TbomEmployeeAssignment, self).write(vals)

    def unlink(self):
        for record in self:
            if record.operation_id.state in ('closed', 'cancelled'):
                raise ValidationError('Cannot delete employee assignments of a closed or cancelled operation.')
        return super(TbomEmployeeAssignment, self).unlink()

    def action_back_to_operation(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'history_back',
        }
