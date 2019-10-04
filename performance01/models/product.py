# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    partner_id = fields.Many2one('res.partner', string="Manufacturer", domain=[('partner_type', '=', 'manufacturer')])
