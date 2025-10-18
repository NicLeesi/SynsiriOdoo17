from odoo import models, fields

class HrSkillType(models.Model):
    _inherit = 'hr.skill.type'

    code = fields.Char(string="Code", help="Technical code for linking with payslip inputs")
