from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField
from wtforms.validators import DataRequired
import requests
import os
from pprint import pprint

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['FLASK_SECRET']
Bootstrap(app)
# Create the Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies-collection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Create Table
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(50), nullable=True)
    img_url = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '<Book %r>' % self.title

db.create_all()

TMDB_APIKEY = os.environ['TMDB_APIKEY']
TMDB_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_GET_MOVIE = "https://api.themoviedb.org/3/movie"
TMDB_IMG_PATH = "https://image.tmdb.org/t/p/w500/"


class EditForm(FlaskForm):
    rating = StringField('Your Rating out of 10 e.g 6.0', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    id = HiddenField('ID')
    submit = SubmitField(label='Submit')


class AddMovie(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField(label='Add Movie')


@app.route("/")
def home():
    # get a list of all movies
    all_movies = Movie.query.order_by(desc(Movie.rating)).all()
    # loop through each object on the list and update the object ranking to the index + 1
    for i in range(len(all_movies)):
        all_movies[i].ranking = i + 1
        db.session.commit()

    return render_template("index.html", all_movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    id = request.args.get('id')
    form = EditForm(id=id)
    movie_to_update = Movie.query.get(id)
    if request.method == 'POST' and form.validate_on_submit():
        movie_id = request.form['id']
        movie_to_update = Movie.query.get(movie_id)
        movie_to_update.rating = request.form['rating']
        movie_to_update.review = request.form['review']
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('edit.html', movie_to_update=movie_to_update, form=form)


@app.route("/delete")
def delete_movie():
    id = request.args.get('id')
    movie_to_delete = Movie.query.get(id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    Add_Form = AddMovie()
    if request.method == 'POST' and Add_Form.validate_on_submit():
        movie_title = Add_Form.title.data
        print(movie_title)
        parameters = {
            'api_key': TMDB_APIKEY,
            'language': 'en-US',
            'query': movie_title
        }
        data = requests.get(url=TMDB_URL, params=parameters)
        response = data.json()['results']
        # for title in response:
        #     pprint(title['original_title'])
        return render_template('select.html', data=response)
    return render_template('add.html', form=Add_Form)


@app.route("/find")
def find_movie():
    movie_id = request.args.get('id')
    parameters = {
        'api_key': TMDB_APIKEY,
        'language': 'en-US',
    }
    data = requests.get(url=f"{TMDB_GET_MOVIE}/{movie_id}", params=parameters)
    response = data.json()
    title = response["original_title"]
    description = response["overview"]
    img_url = f"{TMDB_IMG_PATH}{response['poster_path']}"
    year = response["release_date"].split('-')[0]
    new_movie = Movie(
        title=title,
        year=year,
        description=description,
        img_url=img_url
    )
    db.session.add(new_movie)
    db.session.commit()

    movie_to_edit = Movie.query.filter_by(title=title).first()
    movie_to_edit_id = movie_to_edit.id

    return redirect(url_for('edit', id=movie_to_edit_id))


if __name__ == '__main__':
    app.run(debug=True)
