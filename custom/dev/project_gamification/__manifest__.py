{
    'name': 'Project Gamification',
    'version': '1.0',
    'website': '',
    'category': 'Services/Project',
    'sequence': 45,
    'summary': 'modify projects to suit gamification ',
    'depends': ['project'
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/gamification_goal_challenge.xml",
        "views/importance_type_views.xml",
        "views/project_task_kanban_qc_inherit.xml",
        "views/project_task_views.xml",

    ],

    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
