from flask import Blueprint, render_template, request, redirect, url_for

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # TODO: implement authentication
        # email = request.form.get('email')
        # password = request.form.get('password')
        return redirect(url_for('main.index'))
    return render_template('login.html')


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # TODO: implement user creation and validation
        # name = request.form.get('name')
        # email = request.form.get('email')
        # password = request.form.get('password')
        return redirect(url_for('main.index'))
    return render_template('signup.html')
