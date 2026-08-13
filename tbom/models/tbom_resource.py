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
