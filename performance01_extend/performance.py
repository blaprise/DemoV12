# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.exceptions import UserError


class Performance(models.Model):
    _inherit = "performance"

    @api.model
    def action_performance_export_all(self):
        last_performance_search_ids_str = self.env['res.users'].browse([self._uid]).last_performance_search_ids
        last_performance_search_ids_str = last_performance_search_ids_str.replace('[', '').replace(']', '').replace(' ',
                                                                                                                    '')
        last_performance_search_ids_str = last_performance_search_ids_str.split(',')
        list_ids = []
        if last_performance_search_ids_str:
            for performance_id in last_performance_search_ids_str:
                list_ids.append(int(performance_id))
            ctx = {'active_ids': list_ids}
            return self.with_context(ctx).action_bulk_export()
        return True

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        res = super(Performance, self).search(args, offset, limit, order, count=count)
        current_user = self.env['res.users'].browse([self._uid])
        list_ids = []
        if not count:
            brow_res = super(Performance, self).search(args=args)
            for performance in brow_res:
                list_ids.append(performance.id)
            current_user.write({'last_performance_search_ids': str(list_ids)})
        return res

    @api.multi
    def unlink(self):
        rec_check = False
        for performance in self:
            if performance.lead_id:
                if performance.operator_id and performance.operator_id.partner_type in ['manufacturer', 'distributor',
                                                                                        'operator']:
                    rec_check = True
                if performance.partner_id and performance.partner_id.partner_type in ['manufacturer', 'distributor',
                                                                                      'operator']:
                    rec_check = True
                if performance.distributor_ids:
                    for dist in performance.distributor_ids:
                        if dist.partner_type in ['manufacturer', 'distributor', 'operator']:
                            rec_check = True
            if rec_check:
                raise UserError(_("You can't delete this record as it has Manufaturer or distributor or operator."))
        return super(Performance, self).unlink()
