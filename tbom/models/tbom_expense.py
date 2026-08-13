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
