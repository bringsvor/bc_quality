from openerp import models, api, _, fields

class survey_survey(models.Model):
    _name = "survey.survey"
    _inherit = "survey.survey"

    @api.multi
    def _get_last_completed(self):
        for survey in self:
            last_completed_survey = self.env['survey.user_input'].search([('survey_id','=',survey.id),('state','=','done')], order='date_create desc', limit=1)
            if len(last_completed_survey)==0:
                survey.last_completed = None
            else:
                assert len(last_completed_survey)>0
                survey.last_completed = last_completed_survey[0].date_create

    last_completed = fields.Date('Last completed', compute='_get_last_completed')


class survey_user_input(models.Model):
    _name = "survey.user_input"
    _inherit = "survey.user_input"

    approval_state = fields.Selection([('new', 'New'),
                ('rejected', 'Rejected'),
                ('ok', 'Ok'),
                ('error', 'Error')
        ], default='new')
