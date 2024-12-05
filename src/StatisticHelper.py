import math
import ciw
from collections import namedtuple

ErlangParameter = namedtuple('ErlangParameter', ['k', 'rate'])

class StatisticHelper:

    @staticmethod
    def get_ph_generator_from_rate_and_cov(rate: float, coefficient_of_var: float = 0.3):
        para_1, para_2 = StatisticHelper.fit_hypoexponential(1 / rate, coefficient_of_var)
        c_x = StatisticHelper.get_cox_dist_by_erlang_para_pair(para_1, para_2)
        return lambda x: c_x._sample()

    @staticmethod
    def get_cox_dist_by_erlang_para_pair(erlang_para_A: ErlangParameter, erlang_para_B: ErlangParameter):
        k_tot = erlang_para_A.k + erlang_para_B.k
        probs = [0.] * (k_tot - 1) + [1]
        rates = [erlang_para_A.rate] * erlang_para_A.k + [erlang_para_B.rate] * erlang_para_B.k

        Cx = ciw.dists.Coxian(rates=rates, probs=probs)
        return Cx

    @staticmethod
    def fit_hypoexponential(mean: float, coeff_of_var: float):
        # see PhdThesis Weik, §3.2 (p.29)
        # see also sommereder, 2011
        k = math.ceil(1 / (coeff_of_var ** 2))
        k_A = math.ceil(k / 2)
        k_B = k - k_A

        E_B_star = (((k_A * k_B * (coeff_of_var ** 2)) + math.sqrt(
            k_A * k_B * (((coeff_of_var ** 2) * (k_A + k_B)) - 1))) /
                    (k_A * (1 - ((coeff_of_var ** 2) * k_B))))

        E_A_star = 1

        E_A = mean / (1 + E_B_star)
        E_B = (mean / (E_A_star + E_B_star)) * E_B_star

        rate_A = k_A / E_A
        rate_B = k_B / E_B

        return ErlangParameter(k_A, rate_A), ErlangParameter(k_B, rate_B)


