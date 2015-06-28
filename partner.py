__author__ = 'tbri'

from openerp import models, fields

class res_partner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    prefer_sms = fields.Boolean('Prefer reminder on SMS', default=False)
