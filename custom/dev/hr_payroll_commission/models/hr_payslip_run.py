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
from odoo import fields, models, _
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

class HrComPayslipRun(models.Model):
    """Create new model for getting Com Payslip Batches"""
    _inherit = 'hr.payslip.run'
    _description = 'Com Payslip Batches'


    com_slip_ids = fields.One2many('hr.commission.payslip',
                               'payslip_run_id',
                               string='Com Payslips',
                               help="Choose Com Payslips for Batches")

    com_date_from = fields.Date(
        string='Date From',
        required=True,
        help="Start date for Payslip",
        default=lambda self: fields.Date.to_string(
            (date.today().replace(day=1) - relativedelta(months=1))
        )
    )

    com_date_to = fields.Date(
        string='Date To',
        required=True,
        help="End date for Payslip",
        default=lambda self: fields.Date.to_string(
            (date.today().replace(day=1) - relativedelta(days=1))
        )
    )
