# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class TbomEquipment(models.Model):
    _name = 'tbom.equipment'
    _description = 'TBOM Operation Equipment'
    _order = 'deployment_date desc, id desc'

    name = fields.Char(
        string='Equipment Name',
        required=True
    )
    operation_id = fields.Many2one(
        'tbom.temporary.operation',
        string='Operation',
        required=True,
        ondelete='cascade'
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee'
    )
    deployment_date = fields.Date(
        string='Deployment Date',
        default=fields.Date.context_today
    )
    return_date = fields.Date(
        string='Return Date'
    )
    status = fields.Selection(
        [
            ('planned', 'Planned'),
            ('deployed', 'Deployed'),
            ('returned', 'Returned')
        ],
        string='Status',
        default='planned',
        required=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('operation_id'):
                operation = self.env['tbom.temporary.operation'].browse(vals['operation_id'])
                if operation.state in ('closed', 'cancelled'):
                    raise ValidationError('Cannot add equipment to a closed or cancelled operation.')
        return super(TbomEquipment, self).create(vals_list)

    def write(self, vals):
        for record in self:
            if record.operation_id.state in ('closed', 'cancelled'):
                raise ValidationError('Cannot edit equipment of a closed or cancelled operation.')
            if 'operation_id' in vals:
                new_op = self.env['tbom.temporary.operation'].browse(vals['operation_id'])
                if new_op.state in ('closed', 'cancelled'):
                    raise ValidationError('Cannot move equipment to a closed or cancelled operation.')
        return super(TbomEquipment, self).write(vals)

    def unlink(self):
        for record in self:
            if record.operation_id.state in ('closed', 'cancelled'):
                raise ValidationError('Cannot delete equipment of a closed or cancelled operation.')
        return super(TbomEquipment, self).unlink()

    def action_back_to_operation(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'history_back',
        }
