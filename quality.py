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
        self.last_date = fields.Date.to_string(date.today() - timedelta(days=1))

    @api.one
    def start_survey(self):
        a = self._context['active_id']
        b =  self.env['survey.survey'].browse(a)
        return b.action_start_survey()

    @api.one
    def _calc_next_date(self):
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
