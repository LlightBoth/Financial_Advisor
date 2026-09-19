from flask_wtf import FlaskForm
from wtforms import SubmitField
from app.utils.i18n import _l, I18NTranslations


class BaseLocalizedForm(FlaskForm):
    class Meta:
        def get_translations(self, form):
            return I18NTranslations()


# ----- ConfirmDeleteForm -----
class ConfirmDeleteForm(BaseLocalizedForm):
    submit = SubmitField(_l("common.confirm_delete"))


