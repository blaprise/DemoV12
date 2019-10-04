# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PerformanceReport(models.Model):
    _name = "performance.report"
    _description = "Performance Statistics"
    _auto = False
    _rec_name = 'date'

    date = fields.Date(readonly=True, string="Opened Date")
    date_deadline = fields.Date(readonly=True, string="Expected Closing")
#     date_closed = fields.Date(readonly=True,string="Closed Date")
    activity_closed_date = fields.Date(readonly=True, string="Closed Date")
    manufacturer_id = fields.Many2one('res.partner', string='Manufacturer', readonly=True)
    categ_id = fields.Many2one('product.category', string='Product Category', readonly=True)
    operator_id = fields.Many2one('res.partner', string='Operator', readonly=True)
    description = fields.Many2one('opportunity.description', string="Description")
    user_id = fields.Many2one('res.users', string='Assigned To', readonly=True)
    rate = fields.Float(string="$/Week")
    project_id = fields.Many2one('project.project', string="Project")
    state = fields.Selection([
        ('progress', 'In Progress'),
        ('won', 'Won'),
        ('lost', 'Lost'),
        ('done', 'Work Done'),
    ], string="Status", default="progress")

    opportunity_notes = fields.Text(string="Opportunity Notes")
    notes = fields.Text(string="Notes")
    per_lost_reason = fields.Many2one('crm.lost.reason', string="Reason")

    def _select(self):
        select_str = """
                SELECT min(per.id) as id,
                    lead.date_opened AS date,
                    lead.date_deadline AS date_deadline,
                    per.activity_closed_date AS date_closed,
                    per.partner_id AS manufacturer_id,
                    per.category_id AS categ_id,
                    lead.partner_id AS operator_id,
                    lead.name AS description,
                    lead.user_id AS user_id,
                    per.rate AS rate,
                    lead.project_id AS project_id,
                    per.state AS state,
                    lead.description AS opportunity_notes,
                    per.notes AS notes,
                    per.lost_reason AS per_lost_reason
        """
        return select_str

    def _from(self):
        from_str = """
                performance per
                JOIN crm_lead lead ON lead.id = per.lead_id
        """
        return from_str

    def _group_by(self):
        group_by_str = """
                GROUP BY lead.date_opened, lead.date_deadline, per.activity_closed_date, per.partner_id,
                    per.category_id, lead.partner_id, lead.name, lead.user_id, per.rate, lead.project_id,
                    per.state, lead.description, per.notes, per.lost_reason
        """
        return group_by_str

    @api.model_cr
    def init(self):
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))

    # def init(self, cr):
    #     tools.drop_view_if_exists(cr, self._table)
    #     cr.execute("""CREATE or REPLACE VIEW %s as (
    #         %s
    #         FROM ( %s )
    #         %s
    #         )""" % (self._table, self._select(), self._from(), self._group_by()))
