from datetime import date, timedelta, datetime

__author__ = 'tbri'

from osv import osv, fields

SCHEDULING_FREQUENCIES = [('daily', 'Daily'),
                          ('weekly', 'Weekly'),
                          ('biweekly', 'Bi Weekly'),
                          ('monthly', 'Monthly'),
                          ('quaterly', 'Quaterly'),
                          ('yearly', 'Yearly') ]

class Procedure(osv.Model):
    _name = 'bc_quality.procedure'
    _description = 'A procedure to follow for quality assurance'
    _inherit = ['mail.thread']

    def add_follower(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            mail_followers = self.pool.get('mail.followers')
            follower_id = mail_followers.create(cr, uid, {
                'res_model': 'bc_quality.procedure',
                'res_id' : obj.id,
                'partner_id' : obj.responsible_id.id
            })


    def send_to_responsible(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            print "Sending to ", obj.id, obj.responsible_id.id, obj.description
            mail_mail = self.pool.get('mail.mail')
            mail_id = mail_mail.create(cr, uid, {
                'res_model': 'bc_quality.procedure',
                'res_id': obj.id,
                'subject': 'Please act',
                'body_html': '%s' % obj.description,
                'auto_delete': True,
            }, context=context)

            mail_mail.send(cr, uid, [mail_id], recipient_ids=[obj.responsible_id.id], context=context)



    def _get_last_result(self, cr, uid, ids, field, arg, context=None):
        #start_date = datetime.strptime(session.start_date, "%Y-%m-%d")
        result = {}
        for procedure in self.browse(cr, uid, ids, context=context):
            duration = timedelta( days=(10) )
            last_date = date.today() - duration
            result[procedure.id] = last_date.strftime("%Y-%m-%d")
        self.add_follower(cr, uid, ids, context)
        self.message_post(cr, uid, ids, 'My Subject',
                          'helloooo', context=context)
        #self.send_to_responsible(cr, uid, ids, context)
        return result

    def message_get_subscribers(self, cr, uid, ids, context=None):
        # get the followers from the mail.subscription table
        sub_ids = self.message_get_subscribers_ids(cr, uid, ids, context=context);
        # add the employee and its manager if specified to the subscribed users
        # https://doc.openerp.com/trunk/mail/mail_openchatter_howto/
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.user_id:
                sub_ids.append(obj.user_id)

            if obj.responsible_id:
                sub_ids.append(obj.responsible_id)

        print "USER IDS", sub_ids
        return self.pool.get('res.users').read(cr, uid, sub_ids, context=context)

    def _calc_next_time(self):
        duration = timedelta( days=(10) )
        next_date = date.today() + duration
        return next_date

    def _get_next_time(self, cr, uid, ids, field, arg, context=None):
        assert len(ids) == 1
        result = {}
        for procedure in self.browse(cr, uid, ids, context=context):
            next_date = self._calc_next_time()
            result[procedure.id] = next_date.strftime("%Y-%m-%d")
        return result



    def _set_next_time(self, cr, uid, id, name, value, fnct_inv_arg, context):
        print "SET NEXT TIME", name, value
        # 2014-02-23 17:30:00
        dtdt = datetime.strptime( value, '%Y-%m-%d %H:%M:%S').date()
        next_date = self._calc_next_time()

        if dtdt > next_date:
            return False
            #raise ValueError("Can't postpone activities, only framskunde...")

        print dtdt, next_date, dtdt-next_date
        return True


    _columns = {
        'name' : fields.char('Name', required=True, help='A descriptive name for the procedure to be followed'),
        'responsible_id' : fields.many2one('res.partner', 'Responsible'),
        'description' : fields.text('Description', required=False, help='A description of how to execute the procedure'),
        'values' : fields.one2many('bc_quality.limit', 'procedure_id', string='Values to be measured'),

        'frequency' : fields.selection(SCHEDULING_FREQUENCIES, string='Frequency'),
        'last_result' : fields.function(_get_last_result, type='date', string='Last result'),
        'next_time' : fields.function(fnct=_get_next_time, fnct_inv=_set_next_time, type='date', string='Next test'),
    }

class ControlValue(osv.Model):
    _name = 'bc_quality.value'
    _description = 'A measurement that can be performed'

    _columns = {
        'name' : fields.char('Name', required=True, help='A name for the value')
    }

class Limit(osv.Model):
    _name = 'bc_quality.limit'
    _description = 'A limit value for a measurement'

    _columns = {
        'procedure_id' : fields.many2one('bc_quality.procedure', 'Procedure'),
        'value_id' : fields.many2one('bc_quality.value', 'Value'),
        'limit' : fields.char('Limit')
    }

class Measurement(osv.Model):
    _name = 'bc_quality.measurement'
    _description = 'An actual measurement'

    _columns = {
        'result_id' : fields.many2one('bc_quality.result'),
        'value_id' : fields.many2one('bc_quality.value'),
        'measurement' : fields.char('Measurement')
    }

class Result(osv.Model):
    _name = 'bc_quality.result'
    _description = 'A set of ControlValue values, and a date'

    _columns = {
        'procedure_id' : fields.many2one('bc_quality.procedure'),
        'performed' : fields.date('Performed'),
        # TODO Populate with measurements from procedure
        'mwasurement_ids' :fields.one2many('bc_quality.measurement', 'result_id', 'Measurements'),
        'state' : fields.selection([('draft','Draft'), ('done','Done')], string="State"),
    }

