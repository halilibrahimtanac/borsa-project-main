from wtforms import Form,TextAreaField,StringField,validators,PasswordField,ValidationError,IntegerField
from wtforms.fields.core import SelectField

class LoginForm(Form):
    username = StringField("Username",validators=[validators.DataRequired()])
    password = PasswordField("Password",validators=[validators.DataRequired()])

class SignUpForm(Form):
    name = StringField("Name",validators=[validators.DataRequired(),validators.Length(min=2,max=30)])
    username = StringField("Userame",validators=[validators.DataRequired(),validators.Length(min=5,max=10)])
    email = StringField("E-mail",validators=[validators.DataRequired(),validators.Email()])
    password = PasswordField("Password",validators=[validators.DataRequired(),validators.EqualTo(fieldname="confirm",message="Password doesn't match")])
    confirm = PasswordField("Confirm password",validators=[validators.DataRequired()])
    tc = StringField("TC No",validators=[validators.DataRequired()])
    telephone = StringField("Telephone No(without 0)",validators=[validators.DataRequired()])
    adress = TextAreaField("Adress",validators=[validators.DataRequired()])


class BalanceAdd(Form):
    amount = IntegerField("Money amount",validators=[validators.DataRequired()])

class GoodsForm(Form):
    goods_name = StringField("Goods name",validators=[validators.DataRequired(),validators.Length(min=2,max=10)])
    quantity = IntegerField("Quantity",validators=[validators.DataRequired()])

class SellForm(Form):
    products = SelectField("Products",choices=[])
    quantity = IntegerField("Quantity")
    price = IntegerField("Price")

class BuyForm(Form):
    quantity = IntegerField("Quantity")