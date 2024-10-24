# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohamed Muzammil VP (odoo@cybrosys.com)
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
############################################################################.
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
 
    default_debit = fields.Many2one(
        'account.account',
        config_parameter='ohrms_salary_advance.default_debit_account_id',
        string="Default Debit Account",
        default_model='salary.advance'
    )
    default_credit = fields.Many2one(
        'account.account',
        config_parameter='ohrms_salary_advance.default_credit_account_id',
        string="Default Credit Account",
        default_model='salary.advance'
    )
    default_journal = fields.Many2one(
        'account.journal',
        config_parameter='ohrms_salary_advance.default_journal_id',
        string="Default journal",
        default_model='salary.advance'
    )


    # def set_values(self):
    #     super(ResConfigSettings, self).set_values()
    #     self.env['ir.config_parameter'].sudo().set_param('default_debit_account_id', self.default_debit.id or '0')
    #     self.env['ir.config_parameter'].sudo().set_param('default_credit_account_id', self.default_credit.id or '0')
    #
    # @api.model
    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #
    #     # Retrieve stored IDs
    #     debit = self.env['ir.config_parameter'].sudo().get_param('default_debit_account_id', default=0)
    #     credit = self.env['ir.config_parameter'].sudo().get_param('default_credit_account_id', default=0)
    #
    #     # Log or print the retrieved values
    #     print("Retrieved debit: %s", debit)  # Adjust logging if necessary
    #
    #     # Convert to integer if the retrieved value is a valid ID
    #     if debit.isdigit():
    #         debit = int(debit)
    #     else:
    #         debit = 0  # Handle the case when it's invalid
    #
    #     # The same for credit
    #     if credit.isdigit():
    #         credit = int(credit)
    #     else:
    #         credit = 0
    #
    #     # Update the settings with the existing fields in salary.advance
    #     res.update({
    #         'default_debit': debit and self.env['account.account'].browse(debit) or False,
    #         'default_credit': credit and self.env['account.account'].browse(credit) or False,
    #     })
    #
    #     return res
