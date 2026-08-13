# -*- coding: utf-8 -*-

from odoo import models, fields, api

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
