from MySQLdb.cursors import Cursor
from flask import Flask,render_template
from flask import flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,TextAreaField,StringField,validators,PasswordField,ValidationError
from passlib.hash import sha256_crypt
from functools import wraps
from wtforms.fields.core import IntegerField
import forms,decorator

app = Flask(__name__)
app.secret_key = "borsa"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "borsa"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

#SIGNUP FUNCTION
@app.route("/signup",methods=["GET","POST"])
@decorator.logout_required
def signup():
    signup_form = forms.SignUpForm(request.form)
    if request.method == "POST" and signup_form.validate():
        _name = signup_form.name.data
        _username = signup_form.username.data
        _email = signup_form.email.data
        _password = signup_form.password.data
        _tc = signup_form.tc.data
        _telephone = signup_form.telephone.data
        _adress = signup_form.adress.data

        _cursor = mysql.connection.cursor()
        _query = "INSERT INTO users(name,username,email,password,tc,telephone,adress,user_type) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
        _cursor.execute(_query,(_name,_username,_email,_password,_tc,_telephone,_adress,"regular"))
        mysql.connection.commit()
        _cursor.close()
        flash("Successfully signed up!","success")
        return redirect(url_for("index"))
    else:
        return render_template("signup.html",form = signup_form)

#LOGIN LOGOUT FUNCTIONS
@app.route("/login",methods=["GET","POST"])
@decorator.logout_required
def login():
    login_form = forms.LoginForm(request.form)
    if request.method == "POST" and login_form.validate():
        _username = login_form.username.data
        _password = login_form.password.data

        _cursor = mysql.connection.cursor()
        _query = "SELECT * FROM users WHERE username = %s and password = %s"
        result = _cursor.execute(_query,(_username,_password))
        if result != 0:
            user_data = _cursor.fetchone()

            session["logged_in"] = True
            session["username"] = user_data["username"]
            session["id"] = user_data["id"]
            session["user_type"] = user_data["user_type"]

            return redirect(url_for("index"))
        else:
            flash("Error!","danger")
            return redirect(url_for("login"))
    else:
        return render_template("login.html",form = login_form)

@app.route("/logout")
@decorator.login_required
def logout():
    session.clear()
    flash("Logged out!","success")
    return redirect(url_for("login"))

#REGULAR USER FUNCTIONS
@app.route("/balance",methods=["GET","POST"])
@decorator.login_required
def balance():
    balanceform = forms.BalanceAdd(request.form)
    if  (request.method == "POST" and balanceform.validate()):
        if session["user_type"] == "regular":
            money = balanceform.amount.data

            _cursor = mysql.connection.cursor()
            user = "SELECT * FROM balance_requests WHERE user_id = %s"
            verify = _cursor.execute(user,(session["id"],))
            if verify == 0:
                _cursor2 = mysql.connection.cursor()
                _query2 = "INSERT INTO balance_requests(user_id,amount) VALUES(%s,%s)"
                _cursor2.execute(_query2,(session["id"],money))
                mysql.connection.commit()
                _cursor2.close()
            else:
                user = _cursor.fetchone()
                _cursor3 = mysql.connection.cursor()
                _query3 = "UPDATE balance_requests SET amount = %s WHERE user_id = %s"
                _cursor3.execute(_query3,(int(balanceform.amount.data) + user["amount"],session["id"]))
                mysql.connection.commit()
                _cursor3.close()
            

            flash("Balance request sended!","success")
            return redirect(url_for("balance"))
        else:
            flash("You don't have permission to do this","warning")
            return redirect(url_for("index"))
    else:
        return render_template("balance.html",form = balanceform)

#ADMIN BALANCE FUNCTIONS
@app.route("/brequests")
@decorator.login_required
def brequests():
       if session["user_type"] == "admin":
           _cursor = mysql.connection.cursor()
           _query = "SELECT * FROM balance_requests"
           _cursor.execute(_query)
           data = _cursor.fetchall()

           return render_template("brequests.html",balances = data)
       else:
           flash("You don't have permission to do this","warning")
           return redirect(url_for("index"))

@app.route("/accept/<string:id>",methods=["GET","POST"])
@decorator.login_required
def accept(id):
    if session["user_type"] == "admin":
        _cursor = mysql.connection.cursor()
        select_request = "SELECT * FROM balance_requests WHERE user_id = %s"
        _cursor.execute(select_request,(id,))
        request_user = _cursor.fetchone()

        select_balance = "SELECT * FROM entire_balance WHERE user_id = %s"
        result = _cursor.execute(select_balance,(id,))
        if result != 0:
            balance_user = _cursor.fetchone()
            update_balance = "UPDATE entire_balance SET amount = %s WHERE user_id = %s"
            _cursor.execute(update_balance,(request_user["amount"] + balance_user["amount"],id))
            mysql.connection.commit()
            remove_request = "DELETE FROM balance_requests WHERE user_id = %s"
            _cursor.execute(remove_request,(id,))
            mysql.connection.commit()
            _cursor.close()
            flash("Accepted!","success")
            return redirect(url_for("brequests"))
        else:
            insert_user = "INSERT INTO entire_balance(user_id,amount) VALUES(%s,%s)"
            _cursor.execute(insert_user,(id,request_user["amount"]))
            mysql.connection.commit()
            remove_request = "DELETE FROM balance_requests WHERE user_id = %s"
            _cursor.execute(remove_request,(id,))
            mysql.connection.commit()
            _cursor.close()
            flash("Accepted!","success")
            return redirect(url_for("brequests"))
    else:
        flash("You don't have permission to do this","warning")
        return redirect(url_for("index"))

@app.route("/reject/<string:id>",methods=["GET","POST"])
@decorator.login_required
def reject(id):
    if session["user_type"] == "admin":
        _cursor = mysql.connection.cursor()
        remove_request = "DELETE FROM balance_requests WHERE user_id = %s"
        _cursor.execute(remove_request,(id,))
        mysql.connection.commit()
        _cursor.close()
        flash("Rejected!","danger")
        return redirect(url_for("brequests"))
    else:
        flash("You don't have permission to do this!","warning")
        return redirect(url_for("index"))

#REGULAR USER GOODS FUNCTIONS            
@app.route("/goods",methods=["GET","POST"])
@decorator.login_required
def goods():
    if session["user_type"] == "regular":
        goods_form = forms.GoodsForm(request.form)
        if request.method == "POST" and goods_form.validate():
            goods_name = goods_form.goods_name.data
            quantity = goods_form.quantity.data

            _cursor = mysql.connection.cursor()
            _query = "SELECT * FROM goods_requests WHERE user_id = %s and goods_name = %s"
            result = _cursor.execute(_query,(session["id"],goods_name))
            if result != 0:
                data = _cursor.fetchone()
                _query2 = "UPDATE goods_requests SET quantity = %s WHERE user_id = %s and goods_name = %s"
                _cursor.execute(_query2,(data["quantity"] + int(quantity),session["id"],goods_name))
                mysql.connection.commit()
                _cursor.close()
                flash("Request sended!","success")
                return redirect(url_for("goods"))
            else:
                _query3 = "INSERT INTO goods_requests(user_id,goods_name,quantity) VALUES(%s,%s,%s)"
                _cursor.execute(_query3,(session["id"],goods_name,quantity))
                mysql.connection.commit()
                _cursor.close()
                flash("Request sended!","success")
                return redirect(url_for("goods"))

        else:
            return render_template("goods.html",form = goods_form)
    else:
        flash("You don't have permission to do this!","warning")
        return redirect(url_for("index"))

#ADMIN GOODS FUNCTIONS
@app.route("/grequests",methods=["GET","POST"])
@decorator.login_required
def grequests():
    if session["user_type"] == "admin":
        _cursor = mysql.connection.cursor()
        _query = "SELECT * FROM goods_requests"
        _cursor.execute(_query)
        data = _cursor.fetchall()
        return render_template("grequests.html",goods = data)
    else:
        flash("You don't have permission to do this!","warning")
        return redirect(url_for("index"))



@app.route("/acceptg/<string:id>/<string:name>/<string:quantity>",methods=["GET","POST"])
@decorator.login_required
def acceptg(id,name,quantity):
    if session["user_type"] == "admin":
        _cursor = mysql.connection.cursor()
        _query = "SELECT * FROM entire_goods WHERE user_id = %s and goods_name = %s"
        result = _cursor.execute(_query,(int(id),name))
        if result != 0:
            data = _cursor.fetchone()
            _update = "UPDATE entire_goods SET quantity = %s WHERE user_id = %s and goods_name = %s"
            _cursor.execute(_update,(data["quantity"] + int(quantity),int(id),name))
            _delete = "DELETE FROM goods_requests WHERE user_id = %s and goods_name = %s"
            _cursor.execute(_delete,(int(id),name))
            mysql.connection.commit()
            _cursor.close()
            flash("Accepted!","success")
            return redirect(url_for("grequests"))
        else:
            _insert = "INSERT INTO entire_goods(user_id,goods_name,quantity) VALUES(%s,%s,%s)"
            _cursor.execute(_insert,(int(id),name,int(quantity)))
            _delete = "DELETE FROM goods_requests WHERE user_id = %s and goods_name = %s"
            _cursor.execute(_delete,(int(id),name))
            mysql.connection.commit()
            _cursor.close()
            flash("Accepted!","success")
            return redirect(url_for("grequests"))
    else:
        flash("You don't have permission to do this!","warning")
        return redirect(url_for("index"))

@app.route("/rejectg/<string:id>/<string:name>")
@decorator.login_required
def rejectg(id,name):
    if session["user_type"] == "admin":
        _cursor = mysql.connection.cursor()
        _delete = "DELETE FROM goods_requests WHERE user_id = %s and goods_name = %s"
        _cursor.execute(_delete,(int(id),name))
        mysql.connection.commit()
        _cursor.close()
        flash("Rejected!","danger")
        return redirect(url_for("grequests"))
    else:
        flash("You don't have permission to do this!","warning")
        return redirect(url_for("index"))

#SELL FUNCTION
@app.route("/sell",methods=["GET","POST"])
@decorator.login_required
def sell():
    if session["user_type"] == "regular":
        sellform = forms.SellForm(request.form)
        _cursor = mysql.connection.cursor()
        _query = "SELECT goods_name FROM entire_goods WHERE user_id = %s GROUP BY goods_name"
        _cursor.execute(_query,(int(session["id"]),))
        data = _cursor.fetchall()
        for i in data:
           sellform.products.choices.append(i["goods_name"])
        return render_template("sell.html",form = sellform)
    else:
        flash("You don't have permission to do this!","warning")
        return redirect(url_for("index"))

@app.route("/sell/goods",methods=["GET","POST"])
@decorator.login_required
def sellgoods():
    if request.method == "POST":
        sell_form = forms.SellForm(request.form)
        product = sell_form.products.data
        quantity = sell_form.quantity.data
        price = sell_form.price.data

        _cursor = mysql.connection.cursor()
        _query = "SELECT quantity FROM entire_goods WHERE user_id = %s and goods_name = %s"
        _cursor.execute(_query,(int(session["id"]),product))
        dataE = _cursor.fetchone()
        if quantity <= dataE["quantity"] and quantity > 0:
            _select = "SELECT * FROM market WHERE user_id = %s and goods_name = %s"
            result = _cursor.execute(_select,(int(session["id"]),product))
            if result != 0:
                dataM = _cursor.fetchone()
                _update = "UPDATE market SET quantity = %s , price = %s WHERE user_id = %s and goods_name = %s"
                _cursor.execute(_update,(dataM["quantity"] + quantity,price,int(session["id"]),product))
                _updateE = "UPDATE entire_goods SET quantity = %s WHERE user_id = %s and goods_name = %s"
                _cursor.execute(_updateE,(dataE["quantity"] - quantity,int(session["id"]),product))
                _cursor.execute(_query,(int(session["id"]),product))
                dataS = _cursor.fetchone()
                if dataS["quantity"] == 0:
                    _delete = "DELETE FROM entire_goods WHERE user_id = %s and goods_name = %s"
                    _cursor.execute(_delete,(int(session["id"]),product))
                mysql.connection.commit()
                _cursor.close()
                flash("Updated!","success")
                return redirect(url_for("index"))
            else:
                _insert = "INSERT INTO market(user_id,goods_name,quantity,price) VALUES(%s,%s,%s,%s)"
                _cursor.execute(_insert,(int(session["id"]),product,quantity,price))
                _updateE = "UPDATE entire_goods SET quantity = %s WHERE user_id = %s and goods_name = %s"
                _cursor.execute(_updateE,(dataE["quantity"] - quantity,int(session["id"]),product))
                _cursor.execute(_query,(int(session["id"]),product))
                dataS = _cursor.fetchone()
                if dataS["quantity"] == 0:
                    _delete = "DELETE FROM entire_goods WHERE user_id = %s and goods_name = %s"
                    _cursor.execute(_delete,(int(session["id"]),product))
                mysql.connection.commit()
                _cursor.close()
                flash("Selled!","success")
                return redirect(url_for("index"))
        else:
            flash("Not enough goods!","danger")
            return redirect(url_for("index"))

#MARKET FUNCTION
@app.route("/market",methods=["GET","POST"])
@decorator.login_required
def market():
    _cursor = mysql.connection.cursor()
    _query = "SELECT * FROM market"
    _cursor.execute(_query)
    data = _cursor.fetchall()
    return render_template("market.html",products = data)

@app.route("/buy/<string:goods>",methods=["GET","POST"])
@decorator.login_required
def buy(goods):
    buy_form = forms.BuyForm(request.form)
    if request.method == "POST":
        quantity = buy_form.quantity.data
        _cursor = mysql.connection.cursor()
        _sumQ = "SELECT SUM(quantity) as quantity FROM market WHERE goods_name = %s"
        _cursor.execute(_sumQ,(goods,))
        summary = _cursor.fetchone()
        if quantity > summary["quantity"]:
            flash("You can't buy this amount of goods!","danger")
            return redirect(url_for("index"))
        _lowestP = "SELECT MIN(price) as price FROM market WHERE goods_name = %s"
        _cursor.execute(_lowestP,(goods,))
        lowest_price = _cursor.fetchone()
        _lowestG = "SELECT quantity FROM market WHERE goods_name = %s and price = %s"
        _cursor.execute(_lowestG,(goods,lowest_price["price"]))
        _cheapestQuantity = _cursor.fetchone()
        if quantity >= _cheapestQuantity["quantity"]:
            _seller = "SELECT count(*) as seller FROM market WHERE goods_name = %s"
            _cursor.execute(_seller,(goods,))
            sellers = _cursor.fetchone()
            i = 0
            while i<sellers["seller"] and quantity > 0:
                _balance = "SELECT amount FROM entire_balance WHERE user_id = %s"
                _cursor.execute(_balance,(int(session["id"]),))
                userBalance = _cursor.fetchone()
                _cursor.execute(_lowestP,(goods,))
                lowest_price = _cursor.fetchone()
                _cursor.execute(_lowestG,(goods,lowest_price["price"]))
                _cheapestQuantity = _cursor.fetchone()
                _sellerId = "SELECT user_id FROM market WHERE goods_name = %s and price = %s"
                _cursor.execute(_sellerId,(goods,lowest_price["price"]))
                sellerId = _cursor.fetchone()
                _cursor.execute(_balance,(sellerId["user_id"],))
                sellerBalance = _cursor.fetchone()
                if _cheapestQuantity["quantity"] >= quantity:
                    amount = quantity * lowest_price["price"]
                    if amount <= userBalance["amount"]:
                        _updateBalance = "UPDATE entire_balance SET amount = %s WHERE user_id = %s"
                        _cursor.execute(_updateBalance,(sellerBalance["amount"] + amount,sellerId["user_id"]))
                        _cursor.execute(_updateBalance,(userBalance["amount"] - amount,int(session["id"])))
                        _updateStock = "UPDATE market SET quantity = %s WHERE user_id = %s and goods_name = %s"
                        _cursor.execute(_updateStock,(_cheapestQuantity["quantity"] - quantity,sellerId["user_id"],goods))
                        _verifyMarketStock = "SELECT quantity FROM market WHERE user_id = %s and goods_name = %s"
                        _cursor.execute(_verifyMarketStock,(sellerId["user_id"],goods))
                        leftStock = _cursor.fetchone()
                        if leftStock["quantity"] == 0:
                            _deleteMarket = "DELETE FROM market WHERE user_id = %s and goods_name = %s"
                            _cursor.execute(_deleteMarket,(sellerId["user_id"],goods))
                        _verifyStock = "SELECT * FROM entire_goods WHERE user_id = %s and goods_name = %s"
                        result = _cursor.execute(_verifyStock,(int(session["id"]),goods))
                        if result != 0:
                            _getStock = "SELECT quantity FROM entire_goods WHERE user_id = %s and goods_name = %s"
                            _cursor.execute(_getStock,(int(session["id"]),goods))
                            userStock = _cursor.fetchone()
                            _updateGoods = "UPDATE entire_goods SET quantity = %s WHERE user_id = %s and goods_name = %s"
                            _cursor.execute(_updateGoods,(userStock["quantity"] + quantity,int(session["id"]),goods))
                            mysql.connection.commit()
                            _cursor.close()
                            flash("Goods Bought!","success")
                            return redirect(url_for("index"))
                        else:
                            _insert = "INSERT INTO entire_goods(user_id,goods_name,quantity) VALUES(%s,%s,%s)"
                            _cursor.execute(_insert,(int(session["id"]),goods,quantity))
                            mysql.connection.commit()
                            _cursor.close()
                            flash("Goods added to your inventory!","success")
                            return redirect(url_for("index"))
                    else:
                        flash("Proccess finished!","danger")
                        return redirect(url_for("index"))
                amount = _cheapestQuantity["quantity"] * lowest_price["price"]
                quantity = quantity - _cheapestQuantity["quantity"]
                if amount <= userBalance["amount"]:
                    _updateBalance = "UPDATE entire_balance SET amount = %s WHERE user_id = %s"
                    _cursor.execute(_updateBalance,(userBalance["amount"] - amount,int(session["id"])))
                    _cursor.execute(_updateBalance,(sellerBalance["amount"] + amount,sellerId["user_id"]))
                    _deleteGoods = "DELETE FROM market WHERE user_id = %s and goods_name = %s"
                    _cursor.execute(_deleteGoods,(sellerId["user_id"],goods))
                    _verifyGoods = "SELECT * FROM entire_goods WHERE user_id = %s and goods_name = %s"
                    result = _cursor.execute(_verifyGoods,(int(session["id"]),goods))
                    if result !=0:
                        userStock = _cursor.fetchone()
                        _updateStock = "UPDATE entire_goods SET quantity = %s WHERE user_id = %s and goods_name = %s"
                        _cursor.execute(_updateStock,(_cheapestQuantity["quantity"] + userStock["quantity"],int(session["id"]),goods))
                    else:
                        _insertStock = "INSERT INTO entire_goods(user_id,goods_name,quantity) VALUES(%s,%s,%s)"
                        _cursor.execute(_insertStock,(int(session["id"]),goods,_cheapestQuantity["quantity"]))
                i = i + 1
            mysql.connection.commit()
            _cursor.close()
            flash("Complex proccess finished!","success")
            return redirect(url_for("index"))
        else:
            amount = quantity * lowest_price["price"]
            _balance = "SELECT amount FROM entire_balance WHERE user_id = %s"
            _cursor.execute(_balance,(int(session["id"]),))
            userBalance = _cursor.fetchone()
            if amount <= userBalance["amount"]:
                _updateBalance = "UPDATE entire_balance SET amount = %s WHERE user_id = %s"
                _cursor.execute(_updateBalance,(userBalance["amount"] - amount,int(session["id"])))
                _sellerId = "SELECT user_id FROM market WHERE goods_name = %s and price = %s"
                _cursor.execute(_sellerId,(goods,lowest_price["price"]))
                sellerId = _cursor.fetchone()
                _sellerBalance = "SELECT amount FROM entire_balance WHERE user_id = %s"
                _cursor.execute(_sellerBalance,(sellerId["user_id"],))
                sellerBalance = _cursor.fetchone()
                _cursor.execute(_updateBalance,(sellerBalance["amount"] + amount,sellerId["user_id"]))
                _sellerStock = "SELECT quantity FROM market WHERE user_id = %s and goods_name = %s"
                _cursor.execute(_sellerStock,(sellerId["user_id"],goods))
                sellerStock = _cursor.fetchone()
                _updateSellerStock = "UPDATE market SET quantity = %s WHERE user_id = %s and goods_name = %s"
                _cursor.execute(_updateSellerStock,(sellerStock["quantity"] - quantity,sellerId["user_id"],goods))
                _verifySellerStock = "SELECT quantity FROM market WHERE user_id = %s and goods_name = %s"
                _cursor.execute(_verifySellerStock,(sellerId["user_id"],goods))
                verify = _cursor.fetchone()
                if verify["quantity"] == 0:
                    _deleteFromMarket = "DELETE FROM market WHERE user_id = %s and goods_name = %s"
                    _cursor.execute(_deleteFromMarket,(sellerId["user_id"],goods))
                _select = "SELECT * FROM entire_goods WHERE user_id = %s and goods_name = %s"
                result = _cursor.execute(_select,(int(session["id"]),goods))
                if result != 0:
                    userStock = _cursor.fetchone()
                    _updateUserStock = "UPDATE entire_goods SET quantity = %s WHERE user_id = %s and goods_name = %s"
                    _cursor.execute(_updateUserStock,(userStock["quantity"] + quantity,int(session["id"]),goods))
                    mysql.connection.commit()
                    _cursor.close()
                    flash("Goods bought!","success")
                    return redirect(url_for("index"))
                else:
                    _insert = "INSERT INTO entire_goods(user_id,goods_name,quantity) VALUES (%s,%s,%s)"
                    _cursor.execute(_insert,(int(session["id"]),goods,quantity))
                    mysql.connection.commit()
                    _cursor.close()
                    flash("Goods added to your inventory!","success")
                    return redirect(url_for("index"))
            else:
                flash("Not enough money stranger!","danger")
                return redirect(url_for("index"))
        
    _cursor = mysql.connection.cursor()
    _sum = "SELECT SUM(quantity) AS quantity FROM market WHERE goods_name = %s"
    _cursor.execute(_sum,(goods,))
    sum_data = _cursor.fetchone()
    _price = "SELECT MIN(price) as price FROM market WHERE goods_name = %s" 
    _cursor.execute(_price,(goods,))
    price_data = _cursor.fetchone()
    return render_template("buy.html",form = buy_form,quantity = sum_data["quantity"],product = goods,price = price_data["price"])


@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)