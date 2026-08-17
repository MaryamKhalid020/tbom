# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class TbomExpense(models.Model):
    _name = 'tbom.expense'
    _description = 'TBOM Operation Expense'
    _order = 'date desc, id desc'

    operation_id = fields.Many2one(
        'tbom.temporary.operation',
        string='Operation',
        required=True,
        ondelete='cascade'
    )
    description = fields.Char(
        string='Expense Description',
        required=True
    )
    amount = fields.Float(
        string='Amount',
        required=True
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee'
    )

    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount < 0:
                raise ValidationError('Expense amount must not be negative.')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('operation_id'):
                operation = self.env['tbom.temporary.operation'].browse(vals['operation_id'])
                if operation.state in ('closed', 'cancelled'):
                    raise ValidationError('Cannot add expenses to a closed or cancelled operation.')
        return super(TbomExpense, self).create(vals_list)

    def write(self, vals):
        for record in self:
            if record.operation_id.state in ('closed', 'cancelled'):
                raise ValidationError('Cannot edit expenses of a closed or cancelled operation.')
            if 'operation_id' in vals:
                new_op = self.env['tbom.temporary.operation'].browse(vals['operation_id'])
                if new_op.state in ('closed', 'cancelled'):
                    raise ValidationError('Cannot move expenses to a closed or cancelled operation.')
        return super(TbomExpense, self).write(vals)

    def unlink(self):
        for record in self:
            if record.operation_id.state in ('closed', 'cancelled'):
                raise ValidationError('Cannot delete expenses of a closed or cancelled operation.')
        return super(TbomExpense, self).unlink()

    def action_back_to_operation(self):
        self.ensure_one()
        if self.operation_id:
            return {
                'name': 'Temporary Operation',
                'type': 'ir.actions.act_window',
                'res_model': 'tbom.temporary.operation',
                'view_mode': 'form',
                'res_id': self.operation_id.id,
                'target': 'current',
            }
        return {'type': 'ir.actions.act_window_close'}
