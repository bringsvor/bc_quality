from datetime import date, timedelta, datetime
from decimal import Decimal

__author__ = 'tbri'

from osv import osv, fields

""" Sende epost:

    def _process_wi_email(self, cr, uid, activity, workitem, context=None):
        return self.pool.get('email.template').send_mail(cr, uid,
                                            activity.email_template_id.id,
                                            workitem.res_id, context=context)

 Scheduled action?

        <record model="ir.cron" id="account_analytic_cron">
            <field name="name">Contract expiration reminder</field>
            <field name="interval_number">1</field>
            <field name="interval_type">weeks</field>
            <field name="numbercall">-1</field>
            <field name="doall" eval="False"/>
            <field name="model" eval="'account.analytic.account'"/>
            <field name="function" eval="'cron_account_analytic_account'"/>
            <field name="args" eval="'()'" />
        </record>
    </data>

       def cron_account_analytic_account(self, cr, uid, context=None):


            _logger.debug("Sending reminder to uid %s", user_id)
            self.pool.get('email.template').send_mail(cr, uid, template_id, user_id, force_send=True, context=context)



./account_analytic_analysis/account_analytic_analysis_cron.xml




"""


SCHEDULING_FREQUENCIES = [('daily', 'Daily'),
                          ('weekly', 'Weekly'),
                          ('biweekly', 'Bi Weekly'),
                          ('monthly', 'Monthly'),
                          ('quaterly', 'Quaterly'),
                          ('yearly', 'Yearly') ]


# @TODO Montly should be same time every month,, like quaterly and yearly.
FREQUENCIES_DAYS = {'daily' : 1,
                    'weekly' : 7,
                    'biweekly' : 14,
                    'monthly' : 30,
                    'quaterly' : 91,
                    'yearly' : 365}

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

    def check_draft_result(self, cr, uid, ids, procedure, context):
        """
         There should always be one result in draft mode for this procedure.
           'procedure_id' : fields.many2one('bc_quality.procedure'),
        'performed' : fields.date('Performed'),
        # TODO Populate with measurements from procedure
        'mwasurement_ids' :fields.one2many('bc_quality.measurement', 'result_id', 'Measurements'),
        'name' : fields.function(_get_name, type='string'),
        'state' : fields.selection([('draft','Draft'), ('done','Done')], string="State"),
        """

        measurements_to_do = []
        """
        Measurements

        'result_id' : fields.many2one('bc_quality.result'),
        'value_id' : fields.many2one('bc_quality.value'),
        'measurement' : fields.char('Measurement')
    }
        """


        result_model = self.pool.get('bc_quality.result')
        assert len(ids) == 1

        ids = result_model.search(cr, uid, [('state', '=', 'draft'), ('procedure_id', '=', ids[0])], order='performed' )
        print "DRAFT RESULTS", ids

        max_date = datetime.today()
        for draft_result in result_model.read(cr, uid, ids, ['performed']):
            this_date = datetime.strptime(draft_result['performed'], "%Y-%m-%d")
            if not max_date:
                max_date = this_date
            print "DRAFT RESULT NEXT_TIME", this_date, max_date, this_date > max_date
            if this_date > max_date:
                max_date = this_date

        print "MAX DATE", max_date, datetime.today(), max_date - datetime.today()
        if (max_date - datetime.today())> timedelta( days=180):
            print "NOT CREATING ANY MORE"
            return

        values = {'procedure_id' : procedure.id,
            'performed' : procedure.next_time,
            #    'measurement_ids': [(0,0, {'value_id' : 1, 'measurement' : '123.00'})]
        }

        interval = timedelta( days=(FREQUENCIES_DAYS[procedure.frequency]) )
        new_max_date = max_date
        while (new_max_date - datetime.today())< timedelta( days=180):
            print "TRYING TO CREATE", values
            values['performed'] = new_max_date + interval
            new_max_date += interval
            print "TRYING TO CREATE", values
            res_id = result_model.create(cr, uid, values)
            print "Created enpty res", res_id


            measurement_model = self.pool.get('bc_quality.measurement')
            measurement_ids = []
            for value in procedure.values:
                print "--- DRAFT: VALUE ", value
                # Kanskje det fungerer hvis viewet hadde fungert? (0,0, gurba)
                measurement = {'value_id' : value.id, 'result_id' : res_id}
                meas_id = measurement_model.create(cr, uid, measurement)
                measurement_ids.append((1, meas_id, {}))

            print "MEASUREMENTS TO DO ", measurement_ids

            result_model.write(cr, uid, res_id,{'measurement_ids' :measurement_ids } )


    def get_responsible(self, cr, uid, ids, context=None):
        partner_model = self.pool.get('res.partner')
        for procedure in self.browse(cr, uid, ids, context=context):
            partner_id = procedure.responsible_id.id
            print "Looking for partner ", partner_id
            partner = partner_model.browse(cr, uid, [partner_id,], context=context)
            print "... and found ", partner
            return partner[0]

    def _get_last_result(self, cr, uid, ids, field, arg, context=None):
        #start_date = datetime.strptime(session.start_date, "%Y-%m-%d")
        result = {}
        for procedure in self.browse(cr, uid, ids, context=context):
            duration = timedelta( days=(10) )
            last_date = date.today() - duration
            result[procedure.id] = last_date.strftime("%Y-%m-%d")
            self.check_draft_result(cr, uid, ids, procedure, context)
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

    def _calc_next_time(self, procedure):
        print "FREKVENS", procedure.frequency
        duration = timedelta( days=(FREQUENCIES_DAYS[procedure.frequency]) )
        next_date = date.today() + duration
        return next_date

    def _get_next_time(self, cr, uid, ids, field, arg, context=None):
        assert len(ids) == 1
        result = {}
        for procedure in self.browse(cr, uid, ids, context=context):
            next_date = self._calc_next_time(procedure)
            result[procedure.id] = next_date.strftime("%Y-%m-%d")
        return result



    def _set_next_time(self, cr, uid, id, name, value, fnct_inv_arg, context):
        print "SET NEXT TIME", name, value
        if value == False:
            return False
        # 2014-02-23 17:30:00
        #dtdt = datetime.strptime( value, '%Y-%m-%d %H:%M:%S').date()
        dtdt = datetime.strptime( value, '%Y-%m-%d').date()
        for procedure in self.browse(cr, uid, [id], context=context):
            next_date = self._calc_next_time(procedure)

            if dtdt > next_date:
                return False
            #raise ValueError("Can't postpone activities, only framskunde...")

        print dtdt, next_date, dtdt-next_date
        return True


    _columns = {
        'name' : fields.char('Name', required=True, help='A descriptive name for the procedure to be followed'),
        'responsible_id' : fields.many2one('res.partner', string='Responsible'),
        'description' : fields.text('Description', required=False, help='A description of how to execute the procedure'),
        'values' : fields.one2many('bc_quality.limit', 'procedure_id', string='Values to be measured'),

        'frequency' : fields.selection(SCHEDULING_FREQUENCIES, string='Frequency'),
        'last_result' : fields.function(_get_last_result, type='date', string='Last result'),
        'next_time' : fields.function(fnct=_get_next_time, fnct_inv=_set_next_time, type='date', string='Next test'),
    }

class ControlValue(osv.Model):
    _name = 'bc_quality.value'
    _description = 'A measurement that can be performed'

    def _check_limit(self, cr, uid, ids, field, arg, context=None):
        for value in self.browse(cr, uid, ids, context=context):
            print "CHECK LIMIT", value
            limit_value = value.limit_id.limit
            print "LIMIT VALUE", limit_value
            measurement_value = value.measurement_id.measurement
            print "MEASUREMENT VALUE", measurement_value

            return False # Make them all fail

    _columns = {
        'name' : fields.char('Name', required=True, help='A name for the value'),
        'limit_id' : fields.one2many('bc_quality.limit', 'value_id'),
        'measurement_id' : fields.one2many('bc_quality.measurement', 'value_id'),
        # SKulle det vere ein one2many her??? evt ein reference i Limit og Measurement...
        'inside_limit' : fields.function(_check_limit, type='bool')
    }

class Limit(osv.Model):
    _name = 'bc_quality.limit'
    _description = 'A limit value for a measurement'

    _columns = {
        'procedure_id' : fields.many2one('bc_quality.procedure', 'Procedure'),
        'value_id' : fields.many2one('bc_quality.value', string='Value'),
        'limit' : fields.char('Limit')
    }

class Measurement(osv.Model):
    _name = 'bc_quality.measurement'
    _description = 'An actual measurement'


    def _check_limit(self, cr, uid, ids, field, arg, context=None):
        for measurement in self.browse(cr, uid, ids, context=context):
            print "MEAS CHECK LIMIT", measurement.id.id
            print "MEAS CHECK LIMIT2", measurement.id.value_id.id

            print "MEAS CHECK LIMIT3", measurement.id.value_id.limit_id
            assert len(measurement.id.value_id.limit_id) == 1

            limit_value = measurement.id.value_id.limit_id[0].limit
            print "MEAS LIMIT VALUE", limit_value
            measurement_value = measurement.id.measurement
            print "MEAS MEASUREMENT VALUE", measurement_value

            return False


    #def write(self, cr, uid, ids, fields, context=None):
    #    print "WRITE MEASUREMENT", fields
    #    super(Measurement, self).write(cr, uid, ids, fields, context)

    _columns = {
        'result_id' : fields.many2one('bc_quality.result'),
        'value_id' : fields.many2one('bc_quality.value', string='Value'),
        'measurement' : fields.char('Measurement', required=False),
        'inside_limit' : fields.function(_check_limit, type='bool')
    }

class Result(osv.Model):
    _name = 'bc_quality.result'
    _description = 'A set of ControlValue values, and a date'

    def cron_send_reminder(self, cr, uid, context=None):
        if context is None:
            context = {}
        print "CRON"
        context['base_url'] = self.pool.get('ir.config_parameter').get_param(cr, uid, 'web.base.url')
        context['action_id'] = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'bc_quality', 'action_bc_quality_result')[1]
        template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'bc_quality', 'bc_quality_cron_email_template')[1]
        #for user_id, data in remind.items():
        #    context["data"] = data
        #    _logger.debug("Sending reminder to uid %s", user_id)
        next_week = datetime.now()
        next_week += timedelta(days = 14)

        domain = [('performed', '<', next_week),
            ('state', '!=', 'done')]
        result_ids = self.search(cr, uid, domain, context=context, order='performed asc')
        results = self.browse(cr, uid, result_ids, context)
        responsible_results = {}
        for res in results:
            assert res.responsible_id.email
            if res.responsible_id.prefer_sms:
                assert res.responsible_id.mobile

            if not res.responsible_id in responsible_results:
                responsible_results[res.responsible_id] = []
            responsible_results[res.responsible_id].append(res)

        for responsible_id, results in responsible_results.items():
            context['results'] = results
            if responsible_id.prefer_sms:
                print "SENDING SMS"
                # sms_template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'keysms_template', 'bc_quality_cron_sms_template')[1]
                prox = self.pool.get('keysms.template')
                domain = [('model', '=', 'res.partner')]

                sms_template_ids = prox.search(cr, uid, domain, context=context)
                assert len(sms_template_ids) == 1

                #msg = self.pool.get('keysms.template').render(cr, uid, sms_template_id, user_id, context=context)
                msg = self.pool.get('keysms.template').render(cr, uid, sms_template_ids[0], 'res.partner', responsible_id, context=context)
                self.pool.get('keysms.template').send_sms(cr, uid, msg, [responsible_id.mobile], context)
                print "MSG", msg
            else:
                user_id = responsible_id.id
                self.pool.get('email.template').send_mail(cr, uid, template_id, user_id, force_send=True, context=context)


        return True


    def _get_name(self, cr, uid, ids, field, arg, context=None):
        retval = {}
        for result in self.browse(cr, uid, ids, context=context):
            name = result.procedure_id.name
            name += '_Inst'
            retval[result.id] = name
        return retval

    def _get_responsible(self, cr, uid, ids, field, arg, context=None):
        retval = {}

        procedure_model = self.pool.get('bc_quality.procedure')
        for result in self.browse(cr, uid, ids, context=context):
            procedure_id = result.procedure_id.id
            procedure = procedure_model.browse(cr, uid, procedure_id, context=context)
            responsible = procedure.get_responsible()
            #print "RESPONSIBLE", responsible, responsible._columns
            retval[result.id] = responsible

        return retval

    def _get_responsible_name(self, cr, uid, ids, field, arg, context=None):
        retval = {}
        procedure_model = self.pool.get('bc_quality.procedure')
        for result in self.browse(cr, uid, ids, context=context):
            procedure_id = result.procedure_id.id
            procedure = procedure_model.browse(cr, uid, procedure_id, context=context)
            responsible = procedure.get_responsible()
            #print "RESPONSIBLE", responsible, responsible._columns
            retval[result.id] = responsible.name

        return retval


    def action_draft(self, cr, uid, ids, context=None):
        print "SETTING TO DRAFT"
        return self.write(cr, uid, ids, {'state' : 'draft'})

    def action_error(self, cr, uid, ids, context=None):
        print "SETTING TO ERROR"
        return self.write(cr, uid, ids, {'state' : 'error'})

    def action_done(self, cr, uid, ids, context=None):
        print "SETTING TO DONE"
        measurement_model = self.pool.get('bc_quality.measurement')
        out_of_range = False
        for result in self.browse(cr, uid, ids, context=context):
            for meas in result.measurement_ids:
                print "MEAS1", meas
                meas_value = meas.measurement
                print "MEAS VAL", meas_value
                limit_value = meas.value_id.limit_id[0].limit
                print "LIMIT VAL", limit_value
                # Suppose everything is decimal
                meas_value_dec = Decimal(meas_value)
                limit_value_dec = Decimal(limit_value)
                print "COMPARE", meas_value_dec, limit_value_dec, meas_value_dec>limit_value_dec
                if meas_value_dec>limit_value_dec:
                    out_of_range = True

        if out_of_range:
            nextstate = 'error'
        else:
            nextstate = 'done'

        return self.write(cr, uid, ids, {'state' : nextstate})

    def _get_sequence(self, cr, uid, context=None):
        print "GET SEQUENCE"
        obj_sequence = self.pool.get('ir.sequence')
        return obj_sequence.next_by_code(cr, uid, 'bc_quality.measurement.sequence', context=context)


    _columns = {
        'procedure_id' : fields.many2one('bc_quality.procedure', string='Procedure'),
        'performed' : fields.date('Performed'),
        # TODO Populate with GUs from procedure
        'measurement_ids' :fields.one2many('bc_quality.measurement', 'result_id', string='Measurements'),
        # http://forum.openerp.com/forum/topic34956.html
        'measurement_number' : fields.char('Measurement ID'),
        'name' : fields.function(_get_name, type='char', string='Name'),
        'responsible_id' : fields.function(_get_responsible, type='char', string='Responsible'),
        'responsible_id_name' : fields.function(_get_responsible_name, type='char', string='Responsible person'),
        'state' : fields.selection([('draft','Draft'), ('error', 'Error'), ('done','Done')], string="State"),
    }

    _defaults = {
        'state' : 'draft',
        'measurement_number' : _get_sequence,
    }

