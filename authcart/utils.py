# from django.contrib.auth.tokens import PasswordResetTokenGenerator
# import six  # Correct import of six

# class TokenGenerator(PasswordResetTokenGenerator):
#     def _make_hash_value(self, user, timestamp):
#         # Corrected function name to _make_hash_value
#         return six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(user.is_active)

# generate_token = TokenGenerator()
