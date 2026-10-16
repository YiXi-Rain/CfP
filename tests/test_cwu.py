"""从仓库根目录运行：python -m unittest discover -s tests -v。"""
import contextlib
import copy
import io
import math
import unittest

from CwU import Q, Quantity, c, h_, k, me, get_scientific_notation, unit_str_to_dict


class QuantityTests(unittest.TestCase):
    def setUp(self):
        self.previous = {name: getattr(Q, name) for name in (
            'use_significance', 'use_scientific_notation', 'use_natural_units')}
        Q.configure(use_significance=True, use_scientific_notation=False, use_natural_units=False)

    def tearDown(self):
        Q.configure(**self.previous)

    def test_gram_and_prefixed_units(self):
        for unit, kg in [('g', 1e-3), ('mg', 1e-6), ('kg', 1), ('μg', 1e-9)]:
            with self.subTest(unit=unit):
                self.assertAlmostEqual(Q(1, unit).get_value('kg') / kg, 1)
        self.assertEqual(Q(1, 'dam').get_value('m'), 10)

    def test_micro_aliases(self):
        for unit in ('um', 'μm', 'µm'):
            with self.subTest(unit=unit):
                self.assertAlmostEqual(Q(1, unit).get_value('m'), 1e-6)

    def test_ohm_aliases(self):
        for unit in ('Ω', 'Ω', 'ohm', 'omega'):
            with self.subTest(unit=unit):
                self.assertEqual(Q(1, unit).get_value('V/A'), 1)

    def test_derived_dimensions(self):
        definitions = {'Pa': 'N/m2', 'lx': 'lm/m2', 'F': 'C/V', 'T': 'Wb/m2',
                       'H': 'Wb/A', 'W': 'J/s', 'Gy': 'J/kg', 'kat': 'mol/s',
                       'S': 'A/V'}
        for unit, expression in definitions.items():
            with self.subTest(unit=unit):
                self.assertEqual(Q(1, unit).get_value(expression), 1)

    def test_registered_unit_before_prefix(self):
        self.assertEqual(Q(1, 'mol').unit_str, 'mol')
        self.assertEqual(Q(1, 'h').get_value('s'), 3600)
        self.assertEqual(Q(1, 'min').get_value('s'), 60)

    def test_bad_or_unknown_unit_is_rejected(self):
        for unit in ('metre', 'm$', 'm^', 'm**', '(m', 'm)', 'm1/3', 'm//s',
                     '1000*m', 'm s', '()', 'm+*s', 'metre/metre', 'metre0'):
            with self.subTest(unit=unit), self.assertRaises(ValueError):
                Q(1, unit)

    def test_offset_temperature_is_rejected(self):
        for unit in ('°C', '℃', '°F', '℉'):
            with self.subTest(unit=unit), self.assertRaisesRegex(ValueError, '温度'):
                Q(1, unit)

    def test_dictionary_input_is_validated(self):
        self.assertEqual(Q(1, {'Ω': 1}).get_value('V/A'), 1)
        for units in ({'metre': 0}, {'m$': 1}):
            with self.subTest(units=units), self.assertRaises(ValueError):
                Q(1, units)

    def test_explicit_custom_unit_preserves_name(self):
        q = Q(2, 'metre', allow_unknown_units=True)
        self.assertEqual(q.value, 2)
        self.assertEqual(q.unit_dict, {'metre': 1})
        self.assertEqual(q.get_value('metre'), 2)
        with self.assertRaises(ValueError):
            Q(2, 'm$', allow_unknown_units=True)

    def test_brackets_and_powers(self):
        for unit in ('(m/s)**2', '(m/s)^2', '（m/s）2', 'm2*s-2'):
            with self.subTest(unit=unit):
                self.assertEqual(Q(1, unit).get_value('m2/s2'), 1)
        self.assertEqual(Q(1, 'J/(m/s)').get_value('kg*m/s'), 1)
        self.assertEqual(Q(1, '(m2)0.5').get_value('m'), 1)
        self.assertEqual(Q(1, 'm/s/s').get_value('m/s2'), 1)

    def test_inverse_and_dimensionless_units(self):
        self.assertEqual(Q(1, '/s').get_value('1/s'), 1)
        self.assertEqual(Q(1, 'rad').get_value(''), 1)

    def test_conversion_checks_dimensions(self):
        self.assertEqual(Q(1, 'm').get_value('cm'), 100)
        with self.assertRaises(ValueError):
            Q(1, 'm').get_value('s')
        with self.assertRaises(ValueError):
            Q(1, 'm').get_str('s')

    def test_left_scalar_operations(self):
        self.assertEqual((2 * Q(3, 'm')).get_value('m'), 6)
        self.assertEqual((1 / Q(2, 's')).get_value('Hz'), .5)
        self.assertEqual((1 - Q(.5)).value, .5)
        self.assertEqual((1 + Q(.5)).value, 1.5)
        self.assertEqual(sum([Q(1, 'm'), Q(2, 'm')]).get_value('m'), 3)

    def test_scalar_addition_rejects_dimensions(self):
        for operation in (lambda: Q(1, 'm') + 2, lambda: 2 + Q(1, 'm'),
                          lambda: Q(1, 'm') - 2, lambda: 2 - Q(1, 'm')):
            with self.assertRaises(ValueError):
                operation()

    def test_copy_and_returned_dictionary_are_independent(self):
        original = Q(2, 'm', 4)
        for duplicate in (Q(original), original.copy(), copy.copy(original), +original):
            duplicate.significance = 2
            self.assertEqual(original.significance, 4)
            self.assertEqual(duplicate.value, 2)
        units = original.unit_dict
        units['m'] = 5
        self.assertEqual(original.unit_dict, {'m': 1})
        external = {'m': 1}
        q = Q(1, external)
        external['m'] = 2
        self.assertEqual(q.unit_dict, {'m': 1})

    def test_abs_preserves_magnitude_and_units(self):
        self.assertEqual(abs(Q(-1200, 'm')).get_value('m'), 1200)

    def test_scalar_coefficients_preserve_significance(self):
        q = Q(1.234, 'm', 4)
        for result in (q * 2, 2 * q, q / 2, 2 / q):
            self.assertEqual(result.significance, 4)

    def test_intermediate_value_is_not_rounded(self):
        self.assertAlmostEqual((Q(1.23456789, 'm', 3) * 3).value, 3.70370367)
        self.assertEqual(Q(1.23456789, 'm', 3).get_str('m'), '1.23 m')

    def test_addition_uses_decimal_place(self):
        q = Q(1.23, 'm', 3) + Q(4.5, 'm', 2)
        self.assertEqual(q.get_str('m'), '5.7 m')
        self.assertEqual((Q(1000, 'm', 4) + Q(.1, 'm', 1)).significance, 4)
        q = Q(9.9, 'm', 2) + Q(.1, 'm', 1)
        self.assertEqual(str(q), '10.0 m')

    def test_subtraction_and_cancellation_precision(self):
        q = Q(1.23, 'm', 3) - Q(1.22, 'm', 3)
        self.assertEqual(q.get_str('m'), '0.01 m')
        zero = Q(1.23, 'm', 3) - Q(1.23, 'm', 3)
        self.assertEqual(str(zero), '0.00 m')
        self.assertEqual(zero.get_str('cm'), '0 cm')

    def test_significant_rounding_carry(self):
        self.assertEqual(Q(9.99, significance=2).get_str(), '10')
        with Q.settings(use_scientific_notation=True):
            self.assertEqual(Q(9.99, significance=2).get_str(), '1.0e1')

    def test_scientific_notation_sign_and_small_values(self):
        with Q.settings(use_scientific_notation=True):
            for value, expected in [(1200, '1.20e3'), (-1200, '-1.20e3'),
                                    (1e-20, '1.00e-20'), (0, '0.00e0')]:
                with self.subTest(value=value):
                    self.assertEqual(str(Q(value, significance=3)), expected)
        self.assertEqual(get_scientific_notation(-1200), (-1, 1.2, 3))

    def test_extreme_finite_values(self):
        for value in (1e-300, 1e300, 1e-320):
            with self.subTest(value=value):
                sign, coefficient, power = get_scientific_notation(value)
                self.assertEqual(sign, 1)
                self.assertGreaterEqual(coefficient, 1)
                self.assertLess(coefficient, 10)
                with Q.settings(use_scientific_notation=True):
                    self.assertNotIn('0.00e', str(Q(value, significance=3)))

    def test_get_value_ignores_display_settings(self):
        q = Q(1.23456789, 'm', 3)
        with Q.settings(use_scientific_notation=True, use_significance=False):
            self.assertEqual(q.get_value('m'), 1.23456789)
            self.assertEqual(str(Q(-1200)), '-1.2e3')

    def test_settings_validation_and_restore(self):
        with self.assertRaises(TypeError):
            Q.use_significance = 1
        with self.assertRaises(TypeError):
            Q.configure(use_significance=False, invalid=True)
        self.assertTrue(Q.use_significance)
        with self.assertRaises(AttributeError):
            Q(1).use_scientific_notation = True
        with self.assertRaises(RuntimeError):
            with Q.settings(use_scientific_notation=True):
                raise RuntimeError()
        self.assertFalse(Q.use_scientific_notation)

    def test_existing_constants_after_natural_switch(self):
        with Q.settings(use_natural_units=True):
            new_c = Q(1, 'c')
            self.assertTrue(math.isclose(new_c.get_value('m/s'), c.value, rel_tol=1e-14))
            self.assertTrue(math.isclose((new_c + c).get_value('m/s'), 2 * c.value, rel_tol=1e-14))
            self.assertTrue(math.isclose((c + new_c).get_value('m/s'), 2 * c.value, rel_tol=1e-14))
            self.assertEqual(c.unit_str, 'm/s')

    def test_natural_round_trip_and_target_units(self):
        for unit in ('m', 'kg', 's', 'K', 'J', 'MeV/c2', 'A', 'm/s2'):
            with self.subTest(unit=unit):
                si = Q(1.25, unit)
                natural = si.to_natural()
                self.assertAlmostEqual(natural.get_value(unit), 1.25)
                restored = natural.to_si()
                self.assertEqual(restored.unit_dict, si.unit_dict)
                self.assertAlmostEqual(restored.value / si.value, 1)
        self.assertAlmostEqual(k.to_natural().get_value('J/K'), k.value)
        self.assertEqual(h_.to_natural().unit_dict, {'h_': 1})
        self.assertTrue(math.isclose(h_.to_natural().get_value('h_'), 1, rel_tol=1e-14))
        self.assertTrue(math.isclose(k.to_natural().get_value('k'), 1, rel_tol=1e-14))

    def test_constant_units_and_hour_are_distinct(self):
        from CwU import h
        self.assertEqual(Q(1, 'h').get_value('s'), 3600)
        self.assertEqual(h.unit_dict, Q(1, 'J*s').unit_dict)
        self.assertTrue(math.isclose(Q(1, 'h_').get_value('J*s'), h_.value, rel_tol=1e-14))
        self.assertEqual(Q(1, 'kJ').get_value('J'), 1000)

    def test_switch_does_not_reinterpret_existing_values(self):
        q = Q(1, 'm')
        with Q.settings(use_natural_units=True):
            self.assertEqual(q.get_value('cm'), 100)
        natural = q.to_natural()
        self.assertEqual(natural.get_value('cm'), 100)

    def test_physics_formula(self):
        rest_energy = me * c ** 2
        self.assertAlmostEqual(rest_energy.get_value('MeV'), .510998918, places=7)
        self.assertEqual((rest_energy / (me * c ** 2)).unit_dict, {})

    def test_comparisons_and_unit_errors(self):
        self.assertTrue(Q(1, 'm') == Q(100, 'cm'))
        self.assertTrue(Q(2, 'm') > Q(100, 'cm'))
        self.assertTrue(Q(.5) <= 1)
        self.assertFalse(Q(1, 'm') == 1)
        with self.assertRaises(ValueError):
            Q(1, 'm') < Q(1, 's')

    def test_power_and_original_not_mutated(self):
        q = Q(4, 'm2')
        self.assertEqual((q ** .5).get_value('m'), 2)
        self.assertEqual(q.unit_dict, {'m': 2})
        self.assertEqual(q ** 0, 1)
        with self.assertRaises(ValueError):
            q ** Q(1, 's')

    def test_invalid_values_and_significance(self):
        for value in (math.inf, -math.inf, math.nan):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Q(value)
        for sig in (-1, .5, True):
            with self.subTest(sig=sig), self.assertRaises((ValueError, TypeError)):
                Q(1, significance=sig)

    def test_show_still_returns_self(self):
        q = Q(1, 'm', 3)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = q.show('cm')
        self.assertIs(result, q)
        self.assertEqual(output.getvalue(), '100 cm\n')


if __name__ == '__main__':
    unittest.main()
