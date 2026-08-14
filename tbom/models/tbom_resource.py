# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TbomResource(models.Model):
    _name = 'tbom.resource'
    _description = 'Temporary Operation Resource'

    name = fields.Char(
        string='Resource Name',
        required=True
    )

    resource_type = fields.Selection(
        [
            ('equipment', 'Equipment'),
            ('vehicle', 'Vehicle'),
            ('furniture', 'Furniture'),
            ('it_equipment', 'IT Equipment'),
            ('material', 'Material'),
            ('other', 'Other'),
        ],
        string='Resource Type',
        required=True
    )

    quantity = fields.Integer(
        string='Quantity',
        required=True,
        default=1
    )

    operation_id = fields.Many2one(
        'tbom.temporary.operation',
        string='Operation',
        required=True,
        ondelete='cascade'
    )

    assigned_employee_id = fields.Many2one(
        'hr.employee',
        string='Assigned Employee'
    )

    status = fields.Selection(
        [
            ('planned', 'Planned'),
            ('deployed', 'Deployed'),
            ('returned', 'Returned'),
            ('damaged', 'Lost/Damaged'),
        ],
        string='Status',
        default='planned',
        required=True
    )

    description = fields.Text(
        string='Description'
    )

    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError('Resource quantity must be greater than zero.')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('operation_id'):
                operation = self.env['tbom.temporary.operation'].browse(vals['operation_id'])
                if operation.state in ('closed', 'cancelled'):
                    raise ValidationError('Cannot add resources to a closed or cancelled operation.')
        return super(TbomResource, self).create(vals_list)

    def write(self, vals):
        for record in self:
            if record.operation_id.state in ('closed', 'cancelled'):
                raise ValidationError('Cannot edit resources of a closed or cancelled operation.')
            if 'operation_id' in vals:
                new_op = self.env['tbom.temporary.operation'].browse(vals['operation_id'])
                if new_op.state in ('closed', 'cancelled'):
                    raise ValidationError('Cannot move resources to a closed or cancelled operation.')
        return super(TbomResource, self).write(vals)

    def unlink(self):
        for record in self:
            if record.operation_id.state in ('closed', 'cancelled'):
                raise ValidationError('Cannot delete resources of a closed or cancelled operation.')
        return super(TbomResource, self).unlink()
