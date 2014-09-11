__author__ = 'tbri'

from osv import osv, fields

class res_partner(osv.osv):
    _name = "res.partner"
    _inherit = "res.partner"

    _columns = {
        'prefer_sms' : fields.boolean('Prefer reminder on SMS')
    }

    _defaults = {
        'prefer_sms' : False
    }

res_partner()