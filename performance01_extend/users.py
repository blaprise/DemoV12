# -*- coding: utf-8 -*-
from odoo import fields, models


class res_users(models.Model):
    _inherit = "res.users"

    last_performance_search_ids = fields.Char(string="last_performance_search_ids")
