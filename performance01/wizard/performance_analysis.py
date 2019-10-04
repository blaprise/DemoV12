# -*- coding: utf-8 -*-
from odoo import models, fields


class performance_analysis_excel(models.TransientModel):
    _name = 'performance.analysis.excel'

    data = fields.Binary('File')
    name = fields.Char('Filename', size=256, readonly=True)
