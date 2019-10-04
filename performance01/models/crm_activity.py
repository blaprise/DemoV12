# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from odoo import api, models, fields, _
import logging
import base64
import datetime
from io import BytesIO

_logger = logging.getLogger(__name__)

try:
    import xlwt
except ImportError:
    _logger.debug('Can not import xls writer`.')


class OpportunityDescription(models.Model):
    _name = 'opportunity.description'

    name = fields.Char(string="Opportunity Desc", size=128)

    _sql_constraints = [
        ('name',
         'unique (name)',
         'Duplicate entries not allowed.')
    ]


class Performance(models.Model):
    _name = "performance"

    @api.onchange('state')
    def _compute_payments(self):
        if self.state in ['won', 'lost', 'done']:
            self.activity_closed_date = datetime.datetime.now()

    @api.multi
    def unlink(self):
        rec_check = False
        for performance in self:
            if performance.operator_id and performance.operator_id.partner_type in \
                    ['manufacturer', 'distributor', 'operator']:
                rec_check = True
            if performance.partner_id and performance.partner_id.partner_type in ['manufacturer',
                                                                                  'distributor', 'operator']:
                rec_check = True
            if performance.distributor_ids:
                for dist in performance.distributor_ids:
                    if dist.partner_type in ['manufacturer', 'distributor', 'operator']:
                        rec_check = True
            if rec_check:
                raise UserError(_("You can't delete this record as it has Manufaturer or distributor or operator."))
        return super(Performance, self).unlink()

    def _get_distributor(self):
        context = dict(self._context or {})
        partner_id = context.get('partner', False)
        distributor_ids = []
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            if partner.partner_type and partner.partner_type in ('operator', 'industrial', 'chain'):
                return partner.distributor_ids
            else:
                return distributor_ids
        else:
            return distributor_ids

    partner_id = fields.Many2one('res.partner', string="Manufacturer", domain=[('partner_type', '=', 'manufacturer')])
    category_id = fields.Many2one('product.category', string="Category")
    rate = fields.Float(string="$/Week")
    notes = fields.Text(string="Notes")
    lost_reason = fields.Many2one('crm.lost.reason', string="Reason")
    lead_id = fields.Many2one('crm.lead', ondelete='cascade')
    distributor_ids = fields.Many2many('res.partner', 'performance_distributor_rel', 'performance_id', 'distributor_id',
                                       string="Distributor")
    # default = _get_distributor
    state = fields.Selection([
                ('progress', 'In Progress'),
                ('won', 'Won'),
                ('lost', 'Lost'),
                ('done', 'Work Done'),
            ], string="Status", default="progress", track_visibility='onchange',)

    date_opened = fields.Datetime(string="Opened Date", related="lead_id.date_opened", store=True)
    date_deadline = fields.Date(string="Expected Closing", related="lead_id.date_deadline", store=True)
    date_closed = fields.Datetime(string="Closed", related="lead_id.date_closed", store=True)
    operator_id = fields.Many2one('res.partner', string="Operator", related="lead_id.partner_id", store=True)
    lead_notes = fields.Text(string='Description', related="lead_id.description", store=True)
    user_id = fields.Many2one('res.users', related="lead_id.user_id", store=True)
    project_id = fields.Many2one('project.project', string="Project", related="lead_id.project_id", store=True)
    lead_name = fields.Many2one('opportunity.description', string="Opportunity Description", related="lead_id.name",
                                store=True)

    establishment_id = fields.Many2one('partner.establishment', string="Establishment",
                                       related="operator_id.establishment_id", store=True)
    business_id = fields.Many2one("partner.business", string="Business", related="operator_id.business_id", store=True)
    meal_id = fields.Many2one("partner.meal", string="Nbr.Meals / day", related="operator_id.meal_id", store=True)
    supply_id = fields.Many2one('partner.supply', string="Supply", related="operator_id.supply_id", store=True)
    activity_closed_date = fields.Datetime(string="Activity Close Date")

    @api.model
    def create(self, vals):
        if vals.get('state') and vals.get('state') in ['won', 'lost', 'done']:
            vals['activity_closed_date'] = datetime.datetime.now()
        return super(Performance, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('state') and vals.get('state') in ['won', 'lost', 'done']:
            self.activity_closed_date = datetime.datetime.now()
        return super(Performance, self).write(vals)

    def _get_distributors(self, doc):
        self._cr.execute("select distributor_id from performance_distributor_rel where performance_id = %s", [doc.id])
        values = self._cr.fetchall()
        distributors = ''
        for value in values:
            dist_brw = self.env['res.partner'].search([('id', '=', value[0])])
            distributors += dist_brw.name + ', '
        distributors = distributors[:-2]
        return distributors

    @api.multi
    def show(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Opportunity',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'crm.lead',
            'res_id': self.lead_id.id,
            'view_id': self.env['ir.ui.view'].search([('name', '=', 'crm.form.opportunity.desc')])[0].id
        }

    def _getDate(self, date):
        date = datetime.datetime(date.year, date.month, date.day).date()
        # date = datetime.datetime.strptime(str(date), "%Y-%m-%d %H:%M:%S.%f").date()
        return str(date)

    @api.model
    def action_bulk_export(self):
        # print"Inside Method......................\n\n\n\n", self._context
        # sheet_cnt = 0
        brw = self.env['performance'].browse(self._context.get('active_ids'))
        wb = xlwt.Workbook(encoding='utf-8')
        # buf = cStringIO.StringIO()

        i = j = 0
        font = xlwt.Font()
        font.bold = True
        font.height = 350
        style = xlwt.XFStyle()
        style.font = font
        font1 = xlwt.Font()
        font1.bold = True
        style1 = xlwt.XFStyle()
        style1.font = font1
        ws = wb.add_sheet("Performance Analysis Report", cell_overwrite_ok=True)
        ws.row(0).height_mismatch = True
        ws.row(0).height = 25*20
        ws.write(i, j, 'Performance Analysis Report', style)
        i += 2
        ws.write(i, j, 'Opportunity Description', style1)
        j += 1
        ws.write(i, j, 'Opened Date', style1)
        j += 1
        ws.write(i, j, 'Expected Closing', style1)
        j += 1
        ws.write(i, j, 'Closed', style1)
        j += 1
        ws.write(i, j, 'Operator', style1)
        j += 1
        ws.write(i, j, 'Salesperson', style1)
        j += 1
        ws.write(i, j, 'Project', style1)
        j += 1
        ws.write(i, j, 'Description', style1)
        j += 1
        ws.write(i, j, 'Manufacturer', style1)
        j += 1
        ws.write(i, j, 'Category', style1)
        j += 1
        ws.write(i, j, 'Distributor', style1)
        j += 1
        ws.write(i, j, '$/Week', style1)
        j += 1
        ws.write(i, j, 'Status', style1)
        j += 1
        ws.write(i, j, 'Notes', style1)
        j += 1
        ws.write(i, j, 'Reason', style1)
        j = 0
        i += 1

        for rec in brw:
            if rec.lead_id.name.name:
                ws.write(i, j, rec.lead_id.name.name)
            else:
                ws.write(i, j, '')
            j += 1

            if rec.date_opened:
                ws.write(i, j, self._getDate(rec.date_opened))
            else:
                ws.write(i, j, '')
            j += 1

            if rec.date_deadline:
                ws.write(i, j, rec.date_deadline)
            else:
                ws.write(i, j, '')
            j += 1

            if rec.activity_closed_date:
                ws.write(i, j, self._getDate(rec.activity_closed_date))
            else:
                ws.write(i, j, '')
            j += 1

            if rec.operator_id.name:
                ws.write(i, j, rec.operator_id.name)
            else:
                ws.write(i, j, '')
            j += 1

            if rec.user_id.name:
                ws.write(i, j, rec.user_id.name)
            else:
                ws.write(i, j, '')
            j += 1

            if rec.project_id.name:
                ws.write(i, j, rec.project_id.name)
            else:
                ws.write(i, j, '')
            j += 1

            if rec.lead_notes:
                ws.write(i, j, rec.lead_notes)
            else:
                ws.write(i, j, '')
            j += 1

            if rec.partner_id.name:
                ws.write(i, j, rec.partner_id.name)
            else:
                ws.write(i, j, '')
            j += 1

            if rec.category_id.name:
                ws.write(i, j, rec.category_id.name)
            else:
                ws.write(i, j, '')
            j += 1

            ws.write(i, j, self._get_distributors(rec))
            j += 1

            if rec.rate:
                ws.write(i, j, '$' + str(rec.rate))
            else:
                ws.write(i, j, '')
            j += 1

            if rec.state:
                ws.write(i, j, rec.state)
            else:
                ws.write(i, j, rec.state)
            j += 1

            if rec.notes:
                ws.write(i, j, rec.notes)
            else:
                ws.write(i, j, '')
            j += 1

            if rec.lost_reason.name:
                ws.write(i, j, rec.lost_reason.name)
            else:
                ws.write(i, j, '')
            j = 0
            i += 1

        buf = BytesIO()
        wb.save(buf)
        out = base64.encodestring(buf.getvalue())
        abc = self.env['performance.analysis.excel'].create({'data': out,
                                                            'name': 'preformance_analysis_report.xls', })

        action = self.env.ref('performance01.performance_analysis_xcel_action').read()[0]
        # action['context'] = {'active_id': self.env.context['active_id'],
        #                      'active_model': self.env.context['active_model'],
        #                      'default_name': 'preformance_analysis_report.xls',
        #                      'default_data': out,
        #                      }
        action['res_id'] = abc.id
        return action


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    name = fields.Many2one('opportunity.description', string="Opportunity")
    # default = lambda *a: datetime.datetime.now()
    date_opened = fields.Datetime(string="Opened Date", default=fields.Datetime.now)
    project_id = fields.Many2one('project.project', string="Project")
    performance_id = fields.One2many('performance', 'lead_id', string="Performance")
#     order_line = fields.One2many('sale.order.line', 'order_id', string='Order Lines',
#                                  states={'cancel': [('readonly', True)], 'done': [('readonly', True)]},
#                                  copy=True) , ondelete='cascade'

    @api.multi
    def _convert_opportunity_data(self, cr, uid, lead, customer, team_id=False, context=None):
        res = super(CrmLead, self)._convert_opportunity_data(cr, uid, lead, customer, team_id=False, context=None)
        res['name'] = res['name'].id
        return res

    @api.one
    @api.constrains('stage_id')
    def _check_stage(self):
        stage_ids = self.env['crm.stage'].search([('notification', '=', True)])
        states = [perfo.state for perfo in self.performance_id]
        if self.stage_id in stage_ids:
            if any(state == 'progress' for state in states):
                raise ValidationError(_("Can’t complete the action because one or more record is in progress."))


class CrmStage(models.Model):
    _inherit = "crm.stage"

    notification = fields.Boolean(string="Notification Required")
