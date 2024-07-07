from datetime import date, datetime, time
import babel
from odoo import api, fields, models, tools, _

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    employee_skill_line_ids = fields.One2many('hr.payslip.skill',
                                              'payslip_id',
                                              string='Payslip skill',
                                              copy=True,
                                              help="Com Payslip skill for line")

    goal_line_ids = fields.One2many('hr.payslip.goal',
                                    'payslip_id',
                                    string='Payslip goal',
                                    copy=True,
                                    help="Com Payslip goal for line")

    user_id = fields.Many2one(
        'res.users',
        string="User",
        required=True,
        compute='_compute_user_id',
    )

    @api.depends('employee_id')
    def _compute_user_id(self):
        for record in self:
            if record.employee_id:
                record.user_id = record.employee_id.user_id.id
            else:
                record.user_id = False

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
        for goal in goals.filtered(lambda goal: goal.challenge_id and goal.start_date and goal.end_date):
            day_from = datetime.combine(fields.Date.from_string(date_from),
                                        time.min).date()
            day_to = datetime.combine(fields.Date.from_string(date_to),
                                      time.max).date()
            if goal.start_date >= day_from and goal.end_date <= day_to:
                goal_data = {
                    'definition_id': goal.definition_id.name,
                    'code': 'GOAL',
                    'current': goal.current,
                    'target_goal': goal.target_goal,
                    'completeness': goal.completeness,
                }
                res.append(goal_data)

        return res

    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):
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
                        FROM hr_payslip as hp, hr_payslip_input as pi
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
                        FROM hr_payslip as hp, hr_payslip_worked_days as pi
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
                    FROM hr_payslip as hp, hr_payslip_line as pl
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
        goals_dict = {}
        skills_dict = {}
        result_dict = {}
        rules_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        blacklist = []

        payslip = self.env['hr.payslip'].browse(payslip_id)
        for goal_line_id in payslip.goal_line_ids:
            goals_dict[goal_line_id.code] = goal_line_id
        for employee_skill_line_id in payslip.employee_skill_line_ids:
            skills_dict[employee_skill_line_id.code] = employee_skill_line_id
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line

        skills = Skills(payslip.employee_id.id, skills_dict,self.env)
        goals = Goals(payslip.employee_id.id, goals_dict,self.env)
        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
        inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict,
                                 self.env)
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)
        baselocaldict = {'categories': categories, 'rules': rules,
                         'payslip': payslips, 'worked_days': worked_days,
                         'inputs': inputs, 'skills': skills, 'goals': goals}

        # get the ids of the structures on the contracts and their
        # parent id as well
        contracts = self.env['hr.contract'].browse(contract_ids)
        if len(contracts) == 1 and payslip.struct_id:
            structure_ids = list(
                set(payslip.struct_id._get_parent_structure().ids))
        else:
            structure_ids = contracts.get_all_structures()
        # get the rules of the structure and thier children
        rule_ids = self.env['hr.payroll.structure'].browse(
            structure_ids).get_all_rules()
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
        self.name = _('Salary Slip of %s for %s') % (
            employee.name, tools.ustr(
                babel.dates.format_date(date=ttyme, format='MMMM-y',
                                        locale=locale)))
        self.company_id = employee.company_id
        if not self.env.context.get('contract') or not self.contract_id:
            contract_ids = self.get_contract(employee, date_from, date_to)
            if not contract_ids:
                return
            self.contract_id = self.env['hr.contract'].browse(contract_ids[0])
        if not self.contract_id.struct_id:
            return
        self.struct_id = self.contract_id.struct_id
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

        return