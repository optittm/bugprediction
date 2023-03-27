from statistics import mean
import logging

class Math():
    nb_decimal_numbers = 2

    @classmethod
    def get_rounded_mean(cls, values):
        values_mean = mean(values)
        return round(values_mean, cls.nb_decimal_numbers)

    @classmethod
    def get_rounded_rate(cls, value, total):
        rate = (1. * value / total) * 100
        return round(rate, cls.nb_decimal_numbers)
    
    @classmethod
    def get_rounded_divide(cls, dividend, divisor):
        try:
            quotient = round(dividend / divisor, cls.nb_decimal_numbers)
        except ZeroDivisionError:
            logging.exception("Math:Cannot divide by zero")
            return None
        else:
            return quotient