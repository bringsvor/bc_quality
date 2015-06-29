import json
from openerp import api, fields, models, _
from openerp.exceptions import UserError, RedirectWarning
from datetime import date, timedelta

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



class control_procedure(models.Model):
    _name = 'bc_quality.control_procedure'
    _description = 'A set of values and procedures.'

    name = fields.Char('Name')
    state = fields.Selection([
            ('draft','Draft'),
            ('active', 'Active'),
            ('alarm', 'Alarm'),
            ('pause', 'Paused'),
            ('cancel', 'Cancelled'),
        ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help="Ues")
    kanban_dashboard = fields.Text(compute='_kanban_dashboard')
    #color = fields.Integer('Color Index', default=9)
    color = fields.Integer('Color Index', compute='_calc_color')
    registration_forms = fields.Many2many('survey.survey', string='Registration forms')
    doc_count = fields.Integer('Number of documents', compute='_calc_doc_count')
    type = fields.Selection([
        ('manual', 'Manual'),
        ('recurring', 'Recurring'),
        ('auto', 'Automatic')
    ], string='Type', default='recurring', help='What kind of procedure')
    responsible = fields.Many2one('res.users', 'Responsible')
    frequency = fields.Selection(SCHEDULING_FREQUENCIES, string='Frequency', default='weekly')
    last_date = fields.Date('Last execution', compute='_calc_last_date')
    next_date  = fields.Date('Next execution', compute='_calc_next_date')

    # https://www.odoo.com/fr_FR/forum/help-1/question/odoo-tree-view-each-row-add-button-call-function-return-error-81710
    @api.one
    def _calc_last_date(self):
        last_completed = None
        for survey in self.registration_forms:
            if not survey.last_completed:
                continue

            if not last_completed or last_completed>fields.Date.from_string(survey.last_completed):
                last_completed = fields.Date.from_string(survey.last_completed)

        if not last_completed:
            self.last_date = None
        else:
            self.last_date = fields.Date.to_string(last_completed)

    @api.one
    def start_survey(self):
        a = self._context['active_id']
        b =  self.env['survey.survey'].browse(a)
        return b.action_start_survey()

    @api.one
    def open_action(self):
        if len(self.registration_forms)>0:
	        return self.registration_forms[0].action_start_survey()


    @api.one
    def _calc_next_date(self):
	if not self.last_date:
		# This has never happened.
		self.next_date = fields.Date.today()
		return

        last = fields.Date.from_string(self.last_date)
        calc_next = last + timedelta(days=FREQUENCIES_DAYS[self.frequency])
        if calc_next < date.today():
            calc_next = date.today()

        self.next_date = fields.Date.to_string(calc_next)

    @api.one
    def get_registration_forms(self):
        return [x.id for x in self.registration_forms]

    @api.one
    def _calc_color(self):
        if self.state=='draft':
            self.color = 1
        elif self.state=='active':
            self.color = 2
        elif self.state=='alarm':
            self.color = 9
        else:
            self.color = 0

    @api.one
    def _calc_doc_count(self):
        self.doc_count = 2

    @api.one
    def _kanban_dashboard(self):
        self.kanban_dashboard = json.dumps(self.get_journal_dashboard_datas())


    # TODO Rename
    @api.multi
    def get_journal_dashboard_datas(self):
        return {
            'hei' : 99,
            'registration_forms': [x.public_url for x in self.registration_forms],
        }

    def create_response_and_send_mail(wizard, token, partner_id, email):
        """ Create one mail by recipients and replace __URL__ by link with identification token """
        #set url
        url = wizard.survey_id.public_url

        url = urlparse.urlparse(url).path[1:]  # dirty hack to avoid incorrect urls

        if token:
            url = url + '/' + token

        # post the message
        values = {
            'model': None,
            'res_id': None,
            'subject': wizard.subject,
            'body': wizard.body.replace("__URL__", url),
            'body_html': wizard.body.replace("__URL__", url),
            'parent_id': None,
            'partner_ids': partner_id and [(4, partner_id)] or None,
            'notified_partner_ids': partner_id and [(4, partner_id)] or None,
            'attachment_ids': wizard.attachment_ids or None,
            'email_from': wizard.email_from or None,
            'email_to': email,
        }
        mail_id = mail_mail_obj.create(cr, uid, values, context=context)
        mail_mail_obj.send(cr, uid, [mail_id], context=context)


    @api.multi
    def notify_responsible(self):
        template_id = self.env['ir.model.data'].get_object_reference('bc_quality', 'bc_quality_cron_email_template')[1]
        template = self.env['mail.template'].browse(template_id)
        #context['results'] = results
        for procedure in self:
            if procedure.responsible.prefer_sms:
                print "SENDING SMS"
                # sms_template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'keysms_template', 'bc_quality_cron_sms_template')[1]
                domain = [('model', '=', 'res.partner')]

                sms_template_ids = self.env['keysms.template'].search(domain)
                assert len(sms_template_ids) == 1
                sms_template = sms_template_ids[0]

                #msg = self.pool.get('keysms.template').render(cr, uid, sms_template_id, user_id, context=context)
                #msg = sms_template.render('res.partner', procedure)
                #self.env['keysms.template'].send_sms(msg, [procedure.responsible.mobile])
                sms_template.render_and_send(procedure, [procedure.responsible.mobile])
            else:
                user_id = procedure.responsible.id
                template.send_mail(procedure.id, force_send=True)
