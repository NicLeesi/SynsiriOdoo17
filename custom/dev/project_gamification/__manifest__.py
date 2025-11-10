{
    'name': 'Project Gamification',
    'version': '1.0',
    'website': '',
    'category': 'Services/Project',
    'sequence': 45,
    'summary': 'modify projects to suit gamification ',
    'depends': ['gamification','project'
    ],
    'assets': {
            'web.assets_backend': [
                'project_gamification/static/src/js/form_set_cover.js',
                'project_gamification/static/src/xml/form_set_cover.xml',
                'project_gamification/static/src/xml/image_gallery_widget.xml',
                'project_gamification/static/src/js/image_gallery_widget.js',
                'project_gamification/static/src/js/project_task_kanban_button.js',
                'project_gamification/static/src/xml/project_task_custom_button.xml',

                                           ],
        },
    "data": [
        "security/ir.model.access.csv",
        "data/gamification_goal_challenge.xml",
        "data/ir_cron.xml",
        "views/importance_type_views.xml",
        "views/project_task_kanban_qc_inherit.xml",
        "views/project_task_views.xml",
        "views/gamification_goal_view.xml",
        "views/project_task_kanban_inherit.xml",
    ],

    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
