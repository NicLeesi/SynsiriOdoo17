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


class HrContract(models.Model):
    """
    Employee contract based on the visa, work permits
    allows to configure different Salary structure
    """
    _inherit = 'hr.contract'
    _description = 'Employee Commission Contract'

    com_struct_id = fields.Many2one('hr.payroll.structure',
                                string='Commission Structure',
                                help="Choose Payroll Commission Structure")

    def get_all_com_structures(self):
        """
        @return: the structures linked to the given contracts, ordered by
        hierarchy (parent=False first,then first level children and so on)
        and without duplicate
        """
        com_structures = self.mapped('com_struct_id')
        if not com_structures:
            return []
        # YTI TODO return browse records
        return list(set(com_structures._get_parent_structure().ids))

    # def get_attribute(self, code, attribute):
    #     """Function for return code for Contract"""
    #     return self.env['hr.contract.advantage.template'].search(
    #             [('code', '=', code)],
    #             limit=1)[attribute]
    #
    # def set_attribute_value(self, code, active):
    #     """Function for set code for Contract"""
    #     for contract in self:
    #         if active:
    #             value = self.env['hr.contract.advantage.template'].search(
    #                 [('code', '=', code)], limit=1).default_value
    #             contract[code] = value
    #         else:
    #             contract[code] = 0.0
