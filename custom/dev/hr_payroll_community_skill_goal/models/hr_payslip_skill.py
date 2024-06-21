# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class HrComPayslipSkill(models.Model):
    """Create new model for adding some fields"""
    _name = 'hr.payslip.skill'
    _description = 'Payslip skill'
    _order = 'payslip_id, sequence'

    payslip_id = fields.Many2one('hr.payslip', string='PaySlip',
                                 required=True,
                                 ondelete='cascade', index=True,
                                 help="Choose Payslip for skills")
    sequence = fields.Integer(required=True, index=True, default=10,
                              string="Sequence",
                              help="Sequence for skill")
    code = fields.Char(required=True, string="Code",
                       help="The code that can be used in the salary rules")

    skill_type = fields.Char(string='Skill type',
                                  )
    skill_level = fields.Char(string='Skill level',
                                  )
    level_progress = fields.Float(string='Level progress',
                                  )
