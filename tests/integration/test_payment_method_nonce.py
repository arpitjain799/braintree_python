from tests.test_helper import *

class TestPaymentMethodNonce(unittest.TestCase):
    def test_create_nonce_from_payment_method(self):
        customer_id = Customer.create().customer.id
        credit_card_result = CreditCard.create({
            "customer_id": customer_id,
            "number": "4111111111111111",
            "expiration_date": "05/2014",
        })

        result = PaymentMethodNonce.create(credit_card_result.credit_card.token)

        self.assertTrue(result.is_success)
        self.assertNotEqual(None, result.payment_method_nonce)
        self.assertNotEqual(None, result.payment_method_nonce.nonce)

    def test_create_raises_not_found_when_404(self):
        self.assertRaises(NotFoundError, PaymentMethodNonce.create, "not-a-token")

    def test_find_nonce_shows_details(self):
        config = Configuration(
            environment=Environment.Development,
            merchant_id="integration_merchant_id",
            public_key="integration_public_key",
            private_key="integration_private_key"
        )
        gateway = BraintreeGateway(config)

        nonce = PaymentMethodNonce.find("fake-valid-visa-nonce")

        self.assertEqual("401288", nonce.details["bin"])

    def test_find_nonce_shows_3ds_details(self):
        config = Configuration(
            environment=Environment.Development,
            merchant_id="integration_merchant_id",
            public_key="integration_public_key",
            private_key="integration_private_key"
        )
        gateway = BraintreeGateway(config)

        credit_card = {
            "credit_card": {
                "number": "4111111111111111",
                "expiration_month": "12",
                "expiration_year": "2020"
            }
        }

        nonce = TestHelper.generate_three_d_secure_nonce(gateway, credit_card)
        found_nonce = PaymentMethodNonce.find(nonce)
        three_d_secure_info = found_nonce.three_d_secure_info

        self.assertEqual("CreditCard", found_nonce.type)
        self.assertEqual(nonce, found_nonce.nonce)
        self.assertEqual("Y", three_d_secure_info.enrolled)
        self.assertEqual("authenticate_successful", three_d_secure_info.status)
        self.assertEqual(True, three_d_secure_info.liability_shifted)
        self.assertEqual(True, three_d_secure_info.liability_shift_possible)
        self.assertEqual("test_cavv", three_d_secure_info.cavv)
        self.assertEqual("test_xid", three_d_secure_info.xid)
        self.assertEqual("test_eci", three_d_secure_info.eci_flag)
        self.assertEqual("1.0.2", three_d_secure_info.three_d_secure_version)

    def test_find_nonce_shows_paypal_details(self):
        found_nonce = PaymentMethodNonce.find("fake-google-pay-paypal-nonce")

        self.assertNotEqual(None, found_nonce.details["payer_info"]["first_name"])
        self.assertNotEqual(None, found_nonce.details["payer_info"]["last_name"])
        self.assertNotEqual(None, found_nonce.details["payer_info"]["email"])
        self.assertNotEqual(None, found_nonce.details["payer_info"]["payer_id"])

    def test_find_nonce_shows_venmo_details(self):
        found_nonce = PaymentMethodNonce.find("fake-venmo-account-nonce")

        self.assertEquals("99", found_nonce.details["last_two"])
        self.assertEquals("venmojoe", found_nonce.details["username"])
        self.assertEquals("1234567891234567891", found_nonce.details["venmo_user_id"])

    def test_exposes_null_3ds_info_if_none_exists(self):
        http = ClientApiHttp.create()

        _, nonce = http.get_paypal_nonce({
            "consent-code": "consent-code",
            "access-token": "access-token",
            "options": {"validate": False}
        })

        found_nonce = PaymentMethodNonce.find(nonce)

        self.assertEqual(nonce, found_nonce.nonce)
        self.assertEqual(None, found_nonce.three_d_secure_info)

    def test_find_raises_not_found_when_404(self):
        self.assertRaises(NotFoundError, PaymentMethodNonce.find, "not-a-nonce")

    def test_bin_data_has_commercial(self):
        found_nonce = PaymentMethodNonce.find("fake-valid-commercial-nonce")
        bin_data = found_nonce.bin_data

        self.assertEqual(CreditCard.Commercial.Yes, bin_data.commercial)

    def test_bin_data_has_country_of_issuance(self):
        found_nonce = PaymentMethodNonce.find("fake-valid-country-of-issuance-cad-nonce")
        bin_data = found_nonce.bin_data

        self.assertEqual("CAN", bin_data.country_of_issuance)

    def test_bin_data_debit(self):
        found_nonce = PaymentMethodNonce.find("fake-valid-debit-nonce")
        bin_data = found_nonce.bin_data

        self.assertEqual(CreditCard.Debit.Yes, bin_data.debit)

    def test_bin_data_durbin_regulated(self):
        found_nonce = PaymentMethodNonce.find("fake-valid-durbin-regulated-nonce")
        bin_data = found_nonce.bin_data

        self.assertEqual(CreditCard.DurbinRegulated.Yes, bin_data.durbin_regulated)

    def test_bin_data_issuing_bank(self):
        found_nonce = PaymentMethodNonce.find("fake-valid-issuing-bank-network-only-nonce")
        bin_data = found_nonce.bin_data

        self.assertEqual("NETWORK ONLY", bin_data.issuing_bank)

    def test_bin_data_payroll(self):
        found_nonce = PaymentMethodNonce.find("fake-valid-payroll-nonce")
        bin_data = found_nonce.bin_data

        self.assertEqual(CreditCard.Payroll.Yes, bin_data.payroll)

    def test_bin_data_prepaid(self):
        found_nonce = PaymentMethodNonce.find("fake-valid-prepaid-nonce")
        bin_data = found_nonce.bin_data

        self.assertEqual(CreditCard.Prepaid.Yes, bin_data.prepaid)

    def test_bin_data_unknown_values(self):
        found_nonce = PaymentMethodNonce.find("fake-valid-unknown-indicators-nonce")
        bin_data = found_nonce.bin_data

        self.assertEqual(CreditCard.Commercial.Unknown, bin_data.commercial)
        self.assertEqual(CreditCard.CountryOfIssuance.Unknown, bin_data.country_of_issuance)
        self.assertEqual(CreditCard.Debit.Unknown, bin_data.debit)
        self.assertEqual(CreditCard.DurbinRegulated.Unknown, bin_data.durbin_regulated)
        self.assertEqual(CreditCard.Healthcare.Unknown, bin_data.healthcare)
        self.assertEqual(CreditCard.IssuingBank.Unknown, bin_data.issuing_bank)
        self.assertEqual(CreditCard.Payroll.Unknown, bin_data.payroll)
        self.assertEqual(CreditCard.Prepaid.Unknown, bin_data.prepaid)
        self.assertEqual(CreditCard.ProductId.Unknown, bin_data.product_id)
