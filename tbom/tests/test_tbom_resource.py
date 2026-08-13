# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestTbomResource(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a temporary operation to link the resources to
        cls.operation = cls.env['tbom.temporary.operation'].create({
            'name': 'Test Operation',
            'code': 'OP-TEST-001',
            'operation_type': 'other',
            'location': 'Test Location',
            'start_date': '2026-08-01',
            'end_date': '2026-08-31',
        })

    def test_valid_quantity(self):
        """Test that a resource with a valid quantity (1) is saved successfully."""
        resource = self.env['tbom.resource'].create({
            'name': 'Valid Laptop',
            'resource_type': 'it_equipment',
            'quantity': 1,
            'operation_id': self.operation.id,
        })
        self.assertEqual(resource.quantity, 1)

    def test_zero_quantity(self):
        """Test that a resource with quantity 0 raises a ValidationError."""
        with self.assertRaises(ValidationError):
            self.env['tbom.resource'].create({
                'name': 'Zero Laptop',
                'resource_type': 'it_equipment',
                'quantity': 0,
                'operation_id': self.operation.id,
            })

    def test_negative_quantity(self):
        """Test that a resource with a negative quantity (-1) raises a ValidationError."""
        with self.assertRaises(ValidationError):
            self.env['tbom.resource'].create({
                'name': 'Negative Laptop',
                'resource_type': 'it_equipment',
                'quantity': -1,
                'operation_id': self.operation.id,
            })
