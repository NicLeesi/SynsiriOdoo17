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
from datetime import date, datetime, time
import babel
from dateutil.relativedelta import relativedelta
from pytz import timezone
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

# This will generate 16th of days
# ROUNDING_FACTOR = 16


class PayrollCommission(models.Model):
    """Create new model for getting total Payroll Commission Sheet for an Employee"""
    _name = 'hr.commission.payslip'
    _inherit = 'mail.thread'
    _description = 'Commission Slip'

    com_struct_id = fields.Many2one(comodel_name='hr.payroll.structure',
                                string=' Commission Structure',
                                help='Defines the rules that have to be applied'
                                     ' to this commission payslip, accordingly '
                                     'to the contract chosen. If you let empty '
                                     'the field contract, this field isn\'t '
                                     'mandatory anymore and thus the rules '
                                     'applied will be all the rules set on the '
                                     'commission structure of all contracts of the '
                                     'employee valid for the chosen period')
    name = fields.Char(string='Payslip Name', help="Enter Payslip Name")
    number = fields.Char(string='Reference', copy=False,
                         help="References for Payslip", )
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee',
                                  required=True,
                                  help="Choose Employee for Payslip")
    user_id = fields.Many2one(
        'res.users',
        string="User",
        required=True,
        compute='_compute_user_id',
    )

    date_from = fields.Date(
        string='Date From',
        required=True,
        help="Start date for Payslip",
        default=lambda self: fields.Date.to_string(
            (date.today().replace(day=1) - relativedelta(months=1))
        )
    )

    date_to = fields.Date(
        string='Date To',
        required=True,
        help="End date for Payslip",
        default=lambda self: fields.Date.to_string(
            (date.today().replace(day=1) - relativedelta(days=1))
        )
    )
    # this is chaos: 4 states are defined, 3 are used ('verify' isn't)
    # and 5 exist ('confirm' seems to have existed)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft',
        help="""* When the payslip is created the status is \'Draft\'
                \n* If the payslip is under verification,
                the status is \'Waiting\'.
                \n* If the payslip is confirmed then status is set to \'Done\'.
                \n* When user cancel payslip the status is \'Rejected\'.""")
    line_ids = fields.One2many('hr.commission.payslip.line',
                               'com_slip_id',
                               string=' Commission Payslip Lines',
                               help="Choose Commission Payslip for line")
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, help="Choose Company for line",
                                 default=lambda self: self.env[
                                     'res.company']._company_default_get())
    employee_skill_line_ids = fields.One2many('hr.commission.payslip.skill',
                                           'com_payslip_id',
                                           string='Com Payslip skill',
                                           copy=True,
                                           help="Com Payslip skill for line")
    goal_line_ids = fields.One2many('hr.commission.payslip.goal',
                                           'com_payslip_id',
                                           string='Com Payslip goal',
                                           copy=True,
                                           help="Com Payslip goal for line")
    worked_days_line_ids = fields.One2many('hr.commission.payslip.worked.days',
                                           'com_payslip_id',
                                           string='Commission Payslip Worked Days',
                                           copy=True,
                                           help="Com Payslip worked days for line")
    input_line_ids = fields.One2many('hr.commission.payslip.input',
                                     'commission_payslip_id',
                                     string='Payslip Inputs',
                                     help="Choose Payslip Input")
    paid = fields.Boolean(string='Made Payment Order ? ',
                          copy=False, help="Is Payment Order")
    note = fields.Text(string='Internal Note', help="Description for Payslip")
    contract_id = fields.Many2one('hr.contract', string='Contract',
                                  help="Choose Contract for Payslip")
    details_by_salary_rule_category_ids = fields.One2many(
        comodel_name='hr.commission.payslip.line',
        compute='_compute_details_by_salary_rule_category_ids',
        string='Details by Salary Rule Category', help="Details from the salary"
                                                       " rule category")
    credit_note = fields.Boolean(string='Credit Note',
                                 help="Indicates this payslip has "
                                      "a refund of another")
    payslip_run_id = fields.Many2one('hr.payslip.run',
                                     string='Payslip Batches',
                                     copy=False, help="Choose Payslip Run")
    com_payslip_count = fields.Integer(compute='_compute_commission_payslip_count',
                                   string="Payslip Computation Details",
                                   help="Set Payslip Count")

    @api.depends('employee_id')
    def _compute_user_id(self):
        for record in self:
            if record.employee_id:
                record.user_id = record.employee_id.user_id.id
            else:
                record.user_id = False

    def _compute_details_by_salary_rule_category_ids(self):
        """Compute function for Salary Rule Category for getting
         all Categories"""
        for com_payslip in self:
            com_payslip.details_by_salary_rule_category_ids = com_payslip.mapped(
                'line_ids').filtered(lambda line: line.category_id)

    def _compute_commission_payslip_count(self):
        """Compute function for getting Total count of Payslips"""
        for com_payslip in self:
            com_payslip.com_payslip_count = len(com_payslip.line_ids)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """Function for adding constrains for payslip datas
        by considering date_from and date_to fields"""
        if any(self.filtered(
                lambda payslip: payslip.date_from > payslip.date_to)):
            raise ValidationError(
                _("Payslip 'Date From' must be earlier 'Date To'."))

    def action_com_payslip_done(self):
        """Function for change stage of  com Payslip"""
        self.action_commission_compute_sheet()
        return self.write({'state': 'done'})

    def action_com_payslip_draft(self):
        """Function for change stage of com Payslip"""
        return self.write({'state': 'draft'})

    def action_com_payslip_cancel(self):
        """Function for change stage of Payslip"""
        return self.write({'state': 'cancel'})

    def action_com_refund_sheet(self):
        """Function for refund the com Payslip sheet"""
        for com_payslip in self:
            copied_payslip = com_payslip.copy(
                {'credit_note': True})
            copied_payslip.action_commission_compute_sheet()
            com_payslip.write({'state': 'refund'})
        formview_ref = self.env.ref('hr_payroll_community.hr_commission_payslip_view_form',
                                    False)
        treeview_ref = self.env.ref('hr_payroll_community.hr_commission_payslip_view_tree',
                                    False)
        return {
            'name': _("Refund Commission Payslip"),
            'view_mode': 'tree, form',
            'view_id': False,
            'res_model': 'hr.commission.payslip',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % copied_payslip.ids,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'),
                      (formview_ref and formview_ref.id or False, 'form')],
            'context': {}
        }


    def unlink(self):
        """Function for unlink the Payslip"""
        if any(self.filtered(
                lambda payslip: payslip.state not in ('draft', 'cancel'))):
            raise UserError(
                _('You cannot delete a payslip which is not draft or cancelled!'
                  ))
        return super(PayrollCommission, self).unlink()

    @api.model
    def get_contract(self, employee, date_from, date_to):
        """
        @param employee: recordset of employee
        @param date_from: date_field
        @param date_to: date_field
        @return: returns the ids of all the contracts for the given employee
        that need to be considered for the given dates
        """
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to),
                    ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to),
                    ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the
        # date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|',
                    ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id),
                        ('state', '=', 'open'), '|',
                        '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids


    def action_commission_compute_sheet(self):
        """Function for compute Comslip sheet"""
        for com_payslip in self:
            #Call onchange_contract_id function to get Other input lines
            com_payslip.onchange_contract_id()
            number = com_payslip.number or self.env['ir.sequence'].next_by_code(
                'com.salary.slip')
            # delete old payslip lines
            com_payslip.line_ids.unlink()
            # set the list of contract for which the rules have to be applied
            # if we don't give the contract, then the rules to apply should be
            # for all current contracts of the employee
            contract_ids = com_payslip.contract_id.ids or \
                           self.get_contract(com_payslip.employee_id,
                                             com_payslip.date_from, com_payslip.date_to)
            lines = [(0, 0, line) for line in
                     self._get_com_payslip_lines(contract_ids, com_payslip.id)]
            com_payslip.write({'line_ids': lines, 'number': number})

        return True

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contracts: Browse record of contracts, date_from, date_to
        @return: returns a list of dict containing the input that should be
        applied for the given contract between date_from and date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(
                lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from),
                                        time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to),
                                      time.max)
            # compute leave days
            leaves = {}
            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            day_leave_intervals = contract.employee_id.list_leaves(
                day_from, day_to, calendar=contract.resource_calendar_id)
            multi_leaves = []


            for day, hours, leave in day_leave_intervals:
                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.combine(day, time.min)),
                    tz.localize(datetime.combine(day, time.max)),
                    compute_leaves=False,
                )
                if len(leave) > 1:
                    for each in leave:
                        if each.holiday_id:
                            multi_leaves.append(each.holiday_id)
                else:
                    holiday = leave.holiday_id
                    current_leave_struct = leaves.setdefault(
                        holiday.holiday_status_id, {
                            'name': holiday.holiday_status_id.name or _(
                                'Global Leaves'),
                            'sequence': 5,
                            'code': holiday.holiday_status_id.code or 'GLOBAL',
                            'number_of_days': 0.0,
                            'number_of_hours': 0.0,
                            'contract_id': contract.id,
                        })
                    current_leave_struct['number_of_hours'] += hours
                    if work_hours:
                        current_leave_struct[
                            'number_of_days'] += hours / work_hours
            # compute worked days
            work_data = contract.employee_id.get_work_days_data(
                day_from, day_to, calendar=contract.resource_calendar_id)
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': work_data['days'],
                'number_of_hours': work_data['hours'],
                'contract_id': contract.id,
            }
            res.append(attendances)
            uniq_leaves = [*set(multi_leaves)]
            c_leaves = {}
            for rec in uniq_leaves:
                duration = rec.duration_display.replace("days", "").strip()
                duration_in_hours = float(duration) * 24
                c_leaves.setdefault(rec.holiday_status_id,
                                    {'hours': duration_in_hours})
            for item in c_leaves:
                if not leaves or item not in leaves:
                    data = {
                        'name': item.name,
                        'sequence': 20,
                        'code': item.code or 'LEAVES',
                        'number_of_hours': c_leaves[item]['hours'],
                        'number_of_days': c_leaves[item][
                                              'hours'] / work_hours,
                        'contract_id': contract.id,
                    }
                    res.append(data)
                for time_off in leaves:
                    if item == time_off:
                        leaves[item]['number_of_hours'] += c_leaves[item][
                            'hours']
                        leaves[item]['number_of_days'] \
                            += c_leaves[item]['hours'] / work_hours
            res.extend(leaves.values())
        return res

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        """Function for getting contracts upon date_from and date_to fields"""
        res = []
        com_structure_ids = contracts.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(
            com_structure_ids).get_all_rules()
        sorted_rule_ids = [id for id, sequence in
                           sorted(rule_ids, key=lambda x: x[1])]
        inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped(
            'input_ids')
        for contract in contracts:
            for input in inputs:
                input_data = {
                    'name': input.name,
                    'code': input.code,
                    'contract_id': contract.id,
                    'date_from': date_from,
                    'date_to': date_to,
                }
                res.append(input_data)

        return res

    @api.model
    def get_skill_lines(self, skills):
        """
        @param skills: Browse record of skills from hr.employee.skill.report
        @return: returns a list of dict containing the input that should be
        applied for the given employee skills
        """
        res = []
        # Process only if the skill has a related skill_id
        for skill in skills.filtered(lambda skill: skill.skill_id):
            skill_data = {
                'skill_type': skill.skill_type_id.name,
                'skill_id': skill.skill_id.name,
                'code': 'SKILL',
                'level_progress': skill.level_progress,
                'skill_level': skill.skill_level,
            }
            res.append(skill_data)

        return res

    @api.model
    def get_goal_lines(self, goals, date_from, date_to):
        """
        @param goals: Browse record of goals from module 'gamification.goal'.
        @return: returns a list of dict containing the input that should be
        applied for the given employee commission payslip goals
        """

        res = []
        # Process only if the goal has a related goal_id
        for goal in goals.filtered(lambda goal: goal.challenge_id and goal.start_date):
            day_from = datetime.combine(fields.Date.from_string(date_from),
                                        time.min).date()
            day_to = datetime.combine(fields.Date.from_string(date_to),
                                      time.max).date()
            if goal.start_date <= day_from and (not goal.end_date or day_to <= goal.end_date):
                goal_data = {
                    'definition_id': goal.definition_id.name,
                    'code': goal.code or 'GOAL',
                    'current': goal.current,
                    'target_goal': goal.target_goal,
                    'completeness': goal.completeness,
                    }
                res.append(goal_data)

        return res

    @api.model
    def _get_com_payslip_lines(self, contract_ids, com_payslip_id):
        """Function for getting Payslip Lines"""

        def _sum_salary_rule_category(localdict, category, amount):
            """Function for getting total sum of Salary Rule Category"""
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict,
                                                      category.parent_id,
                                                      amount)
            localdict['categories'].dict[category.code] \
                = category.code in localdict[
                'categories'].dict and localdict['categories'].dict[
                      category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            """Class for Browsable Object"""

            def __init__(self, employee_id, dict, env):
                """Function for getting employee_id,dict and env"""
                self.employee_id = employee_id
                self.dict = dict
                self.env = env

            def __getattr__(self, attr):
                """Function for return dict"""
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for
            usability purposes"""

            def sum(self, code, from_date, to_date=None):
                """Function for getting sum of Payslip with respect to
                 from_date,to_date fields"""
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                        SELECT sum(amount) as sum
                        FROM hr_commission_payslip as hp, hr_commission_payslip_input as pi
                        WHERE hp.employee_id = %s AND hp.state = 'done'
                        AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id =
                        pi.payslip_id AND pi.code = %s""",
                                    (
                                        self.employee_id, from_date, to_date,
                                        code))
                return self.env.cr.fetchone()[0] or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for
            usability purposes"""

            def _sum(self, code, from_date, to_date=None):
                """Function for getting sum of Payslip days with respect to
                 from_date,to_date fields"""
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                            SELECT sum(number_of_days) as number_of_days, 
                            sum(number_of_hours) as number_of_hours
                            FROM hr_commission_payslip as hp, hr_commission_payslip_worked_days as pi
                            WHERE hp.employee_id = %s AND hp.state = 'done'
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = 
                            pi.payslip_id AND pi.code = %s""",
                                    (
                                        self.employee_id, from_date, to_date,
                                        code))
                return self.env.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                """Function for getting sum of Payslip with respect to
                 from_date,to_date fields"""
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                """Function for getting sum of Payslip hours with respect to
                 from_date,to_date fields"""
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for
            usability purposes"""

            def sum(self, code, from_date, to_date=None):
                """Function for getting sum of Payslip with respect to
                 from_date,to_date fields"""
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""SELECT sum(case when hp.credit_note = 
                        False then (pl.total) else (-pl.total) end)
                        FROM hr_commission_payslip as hp, hr_commission_payslip_line as pl
                        WHERE hp.employee_id = %s AND hp.state = 'done'
                        AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id 
                        = pl.slip_id AND pl.code = %s""",
                                    (
                                        self.employee_id, from_date, to_date,
                                        code))
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

        class Skills(BrowsableObject):
            """a class that will be used into the python code, mainly for
            usability purposes"""

            def _sum(self, code):
                """Function for getting sum of Payslip skill """
                self.env.cr.execute("""
                    SELECT sum(level_progress) as level_progress
                    FROM hr_commission_payslip as hcp, hr_commission_payslip_skill as ps
                    WHERE hcp.employee_id = %s
                    AND hcp.id = ps.com_payslip_id AND ps.code = %s
                """, (self.employee_id, code))
                return self.env.cr.fetchone()

        class Goals(BrowsableObject):
            """a class that will be used into the python code, mainly for
            usability purposes"""

        # we keep a dict with the result because a value can be overwritten
        # by another rule with the same code
        result_dict = {}
        rules_dict = {}
        goals_dict = {}
        skills_dict = {}
        inputs_dict = {}
        worked_days_dict = {}
        blacklist = []

        com_payslip = self.env['hr.commission.payslip'].browse(com_payslip_id)
        for goal_line_id in com_payslip.goal_line_ids:
            goals_dict[goal_line_id.code] = goal_line_id
        for employee_skill_line_id in com_payslip.employee_skill_line_ids:
            skills_dict[employee_skill_line_id.code] = employee_skill_line_id
        for worked_days_line in com_payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in com_payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line

        skills = Skills(com_payslip.employee_id.id, skills_dict, self.env)
        goals = Goals(com_payslip.employee_id.id, goals_dict, self.env)
        categories = BrowsableObject(com_payslip.employee_id.id, {}, self.env)
        inputs = InputLine(com_payslip.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(com_payslip.employee_id.id, worked_days_dict,
                                 self.env)
        payslips = Payslips(com_payslip.employee_id.id, com_payslip, self.env)
        rules = BrowsableObject(com_payslip.employee_id.id, rules_dict, self.env)

        baselocaldict = {'categories': categories, 'rules': rules,
                         'payslip': payslips, 'worked_days': worked_days,
                         'inputs': inputs, 'skills': skills, 'goals': goals}

        # get the ids of the structures on the contracts and their

        # get the ids of the structures on the contracts and their
        # parent id as well
        contracts = self.env['hr.contract'].browse(contract_ids)
        if len(contracts) == 1 and com_payslip.com_struct_id:
            com_structure_ids = list(
                set(com_payslip.com_struct_id._get_parent_structure().ids))
        else:
            com_structure_ids = contracts.get_all_structures()
        # get the rules of the structure and thier children
        rule_ids = self.env['hr.payroll.structure'].browse(
            com_structure_ids).get_all_rules()
        # run the rules by sequence
        sorted_rule_ids = [id for id, sequence in
                           sorted(rule_ids, key=lambda x: x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)
        for contract in contracts:
            employee = contract.employee_id
            localdict = dict(baselocaldict, employee=employee,
                             contract=contract)
            for rule in sorted_rules:
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                # check if the rule can be applied
                if rule._satisfy_condition(
                        localdict) and rule.id not in blacklist:
                    # compute the amount of the rule
                    amount, qty, rate = rule._compute_rule(localdict)
                    # check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[
                        rule.code] or 0.0
                    # set/overwrite the amount computed for this rule in
                    # the localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = _sum_salary_rule_category(
                        localdict, rule.category_id, tot_rule - previous_amount)
                    # create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'rate': rate,
                    }
                else:
                    # blacklist this rule and its children
                    blacklist += [id for id, seq in
                                  rule._recursive_search_of_rules()]
        return list(result_dict.values())

    def onchange_employee_id(self, date_from, date_to, employee_id=False,
                             contract_id=False):
        """Function for return worked days when changing onchange_employee_id"""
        # defaults
        res = {
            'value': {
                'line_ids': [],
                # delete old input lines
                'input_line_ids': [(2, x,) for x in self.input_line_ids.ids],
                # delete old worked days lines
                'worked_days_line_ids': [(2, x,) for x in
                                         self.worked_days_line_ids.ids],
                'employee_skill_line_ids': [(2, x,) for x in self.employee_skill_line_ids],
                'goal_line_ids': [(2, x,) for x in self.goal_line_ids],
                # 'details_by_salary_head':[], TODO put me back
                'name': '',
                'contract_id': False,
                'struct_id': False,
            }
        }
        if (not employee_id) or (not date_from) or (not date_to):
            return res
        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        employee = self.env['hr.employee'].browse(employee_id)
        locale = self.env.context.get('lang') or 'en_US'
        res['value'].update({
            'name': _('ComSlip of %s for %s') % (
                employee.name, tools.ustr(
                    babel.dates.format_date(date=ttyme, format='MMMM-y',
                                            locale=locale))),
            'company_id': employee.company_id.id,
        })
        if not self.env.context.get('contract'):
            # fill with the first contract of the employee
            contract_ids = self.get_contract(employee, date_from, date_to)
        else:
            if contract_id:
                # set the list of contract for which the input have to be filled
                contract_ids = [contract_id]
            else:
                # if we don't give the contract, then the input to fill
                # should be for all current contracts of the employee
                contract_ids = self.get_contract(employee, date_from, date_to)
        if not contract_ids:
            return res
        contract = self.env['hr.contract'].browse(contract_ids[0])
        res['value'].update({
            'contract_id': contract.id
        })
        struct = contract.struct_id
        if not struct:
            return res
        res['value'].update({
            'struct_id': struct.id,
        })
        # computation of the salary input
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from,
                                                         date_to)
        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        skills = self.env['hr.employee.skill.report'].search([('employee_id', '=', self.employee_id.id)])
        employee_skill_line_ids = self.get_skill_lines(skills)
        goals = self.env['gamification.goal'].search([('user_id', '=', self.user_id.id)])
        goal_line_ids = self.get_goal_lines(goals, date_from, date_to)

        res['value'].update({
            'worked_days_line_ids': worked_days_line_ids,
            'input_line_ids': input_line_ids,
            'employee_skill_line_ids': employee_skill_line_ids,
            'goal_line_ids': goal_line_ids,
        })
        return res



    @api.onchange('employee_id', )
    def onchange_employee(self):
        """Function for getting contract for employee"""
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        contract_ids = []
        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        locale = self.env.context.get('lang') or 'en_US'
        self.name = _('Commission Slip of %s for %s') % (
            employee.name, tools.ustr(
                babel.dates.format_date(date=ttyme, format='MMMM-y',
                                        locale=locale)))
        self.company_id = employee.company_id
        if not self.env.context.get('contract') or not self.contract_id:
            contract_ids = self.get_contract(employee, date_from, date_to)
            if not contract_ids:
                return
            self.contract_id = self.env['hr.contract'].browse(contract_ids[0])
        if not self.contract_id.com_struct_id:
            return
        self.com_struct_id = self.contract_id.com_struct_id
        if self.contract_id:
            contract_ids = self.contract_id.ids
        # computation of the salary input workday goals skills
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from,
                                                         date_to)
        worked_days_lines = self.worked_days_line_ids.browse([])


        for r in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines

        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        input_lines = self.input_line_ids.browse([])
        for r in input_line_ids:
            input_lines += input_lines.new(r)
        self.input_line_ids = input_lines

        skills = self.env['hr.employee.skill.report'].search([('employee_id', '=', self.employee_id.id)])
        employee_skill_line_ids = self.get_skill_lines(skills)
        employee_skill_line_id = self.employee_skill_line_ids.browse([])
        for r in employee_skill_line_ids:
            employee_skill_line_id += employee_skill_line_id.new(r)
        self.employee_skill_line_ids = employee_skill_line_id

        goals = self.env['gamification.goal'].search([('user_id', '=', self.user_id.id)])
        goal_line_ids = self.get_goal_lines(goals, date_from, date_to)
        goal_line_id = self.goal_line_ids.browse([])
        for r in goal_line_ids:
            goal_line_id += goal_line_id.new(r)
        self.goal_line_ids = goal_line_id

        return

    @api.onchange('contract_id')
    def onchange_contract_id(self):
        """Function for getting structure when changing contract"""
        if not self.contract_id:
            self.com_struct_id = False
        self.with_context(contract=True).onchange_employee()
        return

    def get_salary_line_total(self, code):
        """Function for getting total salary line"""
        self.ensure_one()
        line = self.line_ids.filtered(lambda line: line.code == code)
        if line:
            return line[0].total
        else:
            return 0.0

    @api.onchange('date_from')
    def onchange_date_from(self):
        """Function for getting contract for employee"""
        date_from = self.date_from
        date_to = self.date_to
        contract_ids = []
        if self.contract_id:
            contract_ids = self.contract_id.ids
        # # computation of the salary input
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from,
                                                         date_to)
        worked_days_lines = self.worked_days_line_ids.browse([])
        for r in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines
        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        input_lines = self.input_line_ids.browse([])
        for r in input_line_ids:
            input_lines += input_lines.new(r)
        self.input_line_ids = input_lines
        skills = self.env['hr.employee.skill.report'].search([('employee_id', '=', self.employee_id.id)])
        employee_skill_line_ids = self.get_skill_lines(skills)
        employee_skill_line_id = self.employee_skill_line_ids.browse([])
        for r in employee_skill_line_ids:
            employee_skill_line_id += employee_skill_line_id.new(r)
        self.employee_skill_line_ids = employee_skill_line_id
        goals = self.env['gamification.goal'].search([('user_id', '=', self.user_id.id)])
        goal_line_ids = self.get_goal_lines(goals, date_from, date_to)
        goal_line_id = self.goal_line_ids.browse([])
        for r in goal_line_ids:
            goal_line_id += goal_line_id.new(r)
        self.goal_line_ids = goal_line_id
        if self.line_ids.search([('name', '=', 'Meal Voucher')]):
            self.line_ids.search(
                [('name', '=', 'Meal Voucher')]).salary_rule_id.write(
                {'quantity': self.worked_days_line_ids.number_of_days})
        return

    @api.onchange('date_to')
    def onchange_date_to(self):
        """Function for getting contract for employee"""
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return
        date_from = self.date_from
        date_to = self.date_to
        contract_ids = []
        if self.contract_id:
            contract_ids = self.contract_id.ids
        # computation of the salary input
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from,
                                                         date_to)
        worked_days_lines = self.worked_days_line_ids.browse([])
        for r in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines
        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        input_lines = self.input_line_ids.browse([])
        for r in input_line_ids:
            input_lines += input_lines.new(r)
        self.input_line_ids = input_lines
        skills = self.env['hr.employee.skill.report'].search([('employee_id', '=', self.employee_id.id)])
        employee_skill_line_ids = self.get_skill_lines(skills)
        employee_skill_line_id = self.employee_skill_line_ids.browse([])
        for r in employee_skill_line_ids:
            employee_skill_line_id += employee_skill_line_id.new(r)
        self.employee_skill_line_ids = employee_skill_line_id
        goals = self.env['gamification.goal'].search([('user_id', '=', self.user_id.id)])
        goal_line_ids = self.get_goal_lines(goals, date_from, date_to)
        goal_line_id = self.goal_line_ids.browse([])
        for r in goal_line_ids:
            goal_line_id += goal_line_id.new(r)
        self.goal_line_ids = goal_line_id
        if self.line_ids.search([('name', '=', 'Meal Voucher')]):
            self.line_ids.search(
                [('name', '=', 'Meal Voucher')]).salary_rule_id.write(
                {'quantity': self.worked_days_line_ids.number_of_days})
        return
