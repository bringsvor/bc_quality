# -*- coding: utf-8 -*-
{
    'name' : 'BC Quality',
    'version' : '1.0',
    'category' :  'Quality Management',
    'description' : """
BC Quality


    This module is being developed""",
    'depends' : [
        'survey',
        'base',
        'keysms-openerp',
    ],
    'data' : ['views/quality_dashboard.xml',
              'views/control_procedure_view.xml',
              'views/partner_view.xml',
              'views/survey_views.xml',
              'cron.xml',
	 ]
}
