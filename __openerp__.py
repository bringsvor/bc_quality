# -*- coding: utf-8 -*-

{
    'name' : 'BC Quality',
    'version' : '1.0',
    'category' :  'Quality Management',
    'description' : """
BC Quality


    This module is being developed""",
    'depends' : [
        'mail',
        'email_template',
        'board',
        'base'
    ],
    'data' : ['views/quality_view.xml',
              'quality_board.xml',
              'workflow/workflow.xml',
              'cron.xml'
	 ]
}
