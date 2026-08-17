# -*- coding: utf-8 -*-
from odoo import models, fields


class TemporaryOperationStateHistory(models.Model):
    _name = 'tbom.operation.state.history'
    _description = 'Temporary Operation State Transition History'
    _order = 'transition_datetime desc, id desc'

    operation_id = fields.Many2one(
        'tbom.temporary.operation',
        string='Operation',
        required=True,
        ondelete='cascade'
    )

    previous_state = fields.Selection(
        [
            ('planned', 'Planned'),
            ('setup', 'Setup'),
            ('active', 'Active'),
            ('closing', 'Closing'),
            ('closed', 'Closed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Previous State'
    )

    new_state = fields.Selection(
        [
            ('planned', 'Planned'),
            ('setup', 'Setup'),
            ('active', 'Active'),
            ('closing', 'Closing'),
            ('closed', 'Closed'),
            ('cancelled', 'Cancelled'),
        ],
        string='New State',
        required=True
    )

    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        required=True
    )

    transition_datetime = fields.Datetime(
        string='Date & Time',
        default=fields.Datetime.now,
        required=True
    )

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
