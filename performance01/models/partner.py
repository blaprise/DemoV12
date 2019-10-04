# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import api, fields, models, _


class PartnerRegion(models.Model):
    _name = "partner.region"
    _description = "Partners Regions"

    name = fields.Char(string="Region", size=128)

    _sql_constraints = [
        ('name',
         'unique (name)',
         'Duplicate entries not allowed.')
    ]


class PartnerEstablishment(models.Model):
    _name = "partner.establishment"
    _description = "Partner Establishments"

    name = fields.Char(string="Establishment", size=128)

    _sql_constraints = [
        ('name',
         'unique (name)',
         'Duplicate entries not allowed.')
    ]


class PartnerMeal(models.Model):
    _name = "partner.meal"
    _description = "Partner Meals"

    name = fields.Char(string="Nbr.Meals/day", size=128)

    _sql_constraints = [
        ('name',
         'unique (name)',
         'Duplicate entries not allowed.')
    ]


class PartnerBusiness(models.Model):
    _name = "partner.business"
    _description = "Partner Business"

    name = fields.Char(string="Business", size=128)

    _sql_constraints = [
        ('name',
         'unique (name)',
         'Duplicate entries not allowed.')
    ]


class PartnerSupply(models.Model):
    _name = "partner.supply"
    _description = "Partner Supply"

    name = fields.Char(string="Supply", size=128)

    _sql_constraints = [
        ('name',
         'unique (name)',
         'Duplicate entries not allowed.')
    ]


class PartnerOperator(models.Model):
    _name = "partner.operator"
    _description = "Partner Operator"

    name = fields.Char(string="Group operator", size=128)

    _sql_constraints = [
        ('name',
         'unique (name)',
         'Duplicate entries not allowed.')
    ]


class PartnerGroup(models.Model):
    _name = "partner.group"
    _description = "Partner Group"

    name = fields.Char(string="Group", size=128)

    _sql_constraints = [
        ('name',
         'unique (name)',
         'Duplicate entries not allowed.')
    ]


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Partner'

    partner_type = fields.Selection([
        ('manufacturer', 'Manufacturer'),
        ('distributor', 'Distributor'),
        ('operator', 'Operator'),
        ('industrial', 'Industrial'),
        ('chain', 'Chain'),
    ], string="Type")
    region_ids = fields.Many2many('partner.region', 'partner_region_rel',
                                  'partner_id', 'region_id',
                                  string="Region(s) served")
    establishment_id = fields.Many2one('partner.establishment',
                                       string="Establishment")
    meal_id = fields.Many2one("partner.meal", string="Nbr.Meals / day")
    business_id = fields.Many2one("partner.business", string="Business")
    distributor_ids = fields.Many2many('res.partner',
                                       'partner_distributor_rel',
                                       'partner_id', 'distributor_id',
                                       string="Distributor",
                                       domain=[
                                           ('company_type', '=', 'company'),
                                           ('partner_type', '=', 'distributor')
                                       ])
    operator_ids = fields.Many2many('partner.operator', 'partner_operator_rel', 'partner_id', 'operator_id',
                                    string="Group Operator")
    supply_id = fields.Many2one('partner.supply', string="Supply")
    group_ids = fields.Many2many('partner.group', 'partner_group_rel', 'partner_id', 'group_id', string="Group")
    activity_count = fields.Integer("# Activities", compute='_compute_activities')

    @api.multi
    def _compute_activities(self):
        for partner in self:
            domain = []
            if partner.partner_type == 'operator':
                domain = [('operator_id', 'in', partner.ids)]
            elif partner.partner_type == 'manufacturer':
                domain = [('partner_id', 'in', partner.ids)]
            elif partner.partner_type == 'distributor':
                domain = [('distributor_ids', 'in', partner.ids)]
            else:
                domain = [('operator_id', 'in', partner.ids)]
            activities_ids = self.env['performance'].search(domain)

            partner.activity_count = len(activities_ids)

    @api.multi
    def unlink(self):
        for partner in self:
            if partner.partner_type in ['manufacturer', 'distributor', 'operator']:
                performance_search = self.env['performance'].search([('partner_id', '=', partner.id) or
                                                                     ('operator_id', '=', partner.id)])
                if performance_search:
                    raise UserError(_("You can't delete this record as it is linked with activities."))
                self._cr.execute("""SELECT performance_id FROM performance_distributor_rel WHERE distributor_id=%s""",
                                 (partner.id,))
                res = self._cr.fetchone()
                if res:
                    raise UserError(_("You can't delete this record as it is linked with activities."))
        return super(ResPartner, self).unlink()

    @api.multi
    def write(self, vals):
        if vals.get('partner_type'):
            rec_search = self.env['crm.lead'].search([('partner_id', '=', self.id)])
            if rec_search:
                raise UserError(_('You cannot change type as it is linked with activities.'))
            performance_search = self.env['performance'].search([('partner_id', '=', self.id) or
                                                                 ('operator_id', '=', self.id)])
            if performance_search:
                raise UserError(_('You cannot change type as it is linked with activities.'))
            self._cr.execute("""SELECT performance_id FROM performance_distributor_rel WHERE distributor_id=%s""",
                             (self.id,))
            res = self._cr.fetchone()
            if res:
                raise UserError(_('You cannot change type as it is linked with activities.'))
        return super(ResPartner, self).write(vals)

    @api.multi
    def activities_detail(self):
        if self.partner_type == 'operator':
            domain = str([('operator_id', 'in', self.ids)])
        elif self.partner_type == 'manufacturer':
            domain = str([('partner_id', 'in', self.ids)])
        elif self.partner_type == 'distributor':
            domain = str([('distributor_ids', 'in', self.ids)])
        else:
            domain = str([('operator_id', 'in', self.ids)])

        return {
            'type': 'ir.actions.act_window',
            'name': _('Activities Detail'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'performance',
            'domain': domain,
            'view_id': self.env['ir.ui.view'].search([('name', '=', 'performance.report.tree')])[0].id
        }
