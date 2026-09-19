from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField, FloatField, DateField, TextAreaField
from wtforms.validators import DataRequired, Optional, NumberRange

from app.models import Plan
from app.utils.i18n import _l, I18NTranslations


class BaseLocalizedForm(FlaskForm):
    class Meta:
        def get_translations(self, form):
            return I18NTranslations()


class PlanForm(BaseLocalizedForm):
    goal = StringField(
        _l("plan.goal"), 
        validators=[DataRequired(message=_l("validation.required"))],
        render_kw={"placeholder": _l("plan.goal_placeholder")}
    )
    in_between = DateField(
        _l("plan.target_date"), 
        validators=[DataRequired(message=_l("validation.required"))],
    )
    description = TextAreaField(
        _l("common.description"),
        validators=[Optional()],
        render_kw={"placeholder": _l("plan.description_placeholder")}
    )
    goal_cost = FloatField(
        _l("plan.goal_cost"),
        validators=[
            DataRequired(message=_l("validation.required")),
            NumberRange(min=0.01, message=_l("validation.budget_positive"))
        ],
        render_kw={"placeholder": _l("plan.cost_placeholder")}
    )
    value = BooleanField(_l("plan.status"), default=True)
    
    submit = SubmitField(_l("plan.launch_strategy"))


# ----- EditPlanForm -----
class EditPlanForm(BaseLocalizedForm):
    goal = StringField(
        _l("plan.goal"), 
        validators=[DataRequired(message=_l("validation.required"))],
        render_kw={"placeholder": _l("plan.goal_placeholder")}
    )
    in_between = DateField(
        _l("plan.target_date"), 
        validators=[DataRequired(message=_l("validation.required"))],
    )
    description = TextAreaField(
        _l("common.description"),
        validators=[Optional()],
        render_kw={"placeholder": _l("plan.description_placeholder")}
    )
    goal_cost = FloatField(
        _l("plan.goal_cost"),
        validators=[
            DataRequired(message=_l("validation.required")),
            NumberRange(min=0.01, message=_l("validation.budget_positive"))
        ],
        render_kw={"placeholder": _l("plan.cost_placeholder")}
    )
    value = BooleanField(
        _l("plan.status")
    )
    
    submit = SubmitField(_l("plan.update_strategy"))

    def __init__(self, original_plan: Plan, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_plan = original_plan


# ----- ConfirmDeleteForm -----
class ConfirmDeleteForm(BaseLocalizedForm):
    submit = SubmitField(_l("common.confirm_delete"))

