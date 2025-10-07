from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from pandas.io.sas.sas_constants import column_name_text_subheader_length
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests,os
from dotenv import load_dotenv
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

URL = "https://api.themoviedb.org/3/search/movie"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=False, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)



with app.app_context():
    db.create_all()


class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")



@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating.desc()).all()

    for i in range(len(all_movies)):
        all_movies[i].ranking = i+1

    db.session.commit()
    return render_template("index.html",movies=all_movies)


@app.route("/update/<int:id>",methods=["GET","POST"])
def update(id):
    form = RateMovieForm()
    movie = Movie.query.get(id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html',edit_movie=movie,form=form)



@app.route("/delete/<int:id>")
def delete(id):
    movie = Movie.query.get(id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


class FindMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

@app.route('/add',methods=["GET","POST"])
def add():
    form = FindMovieForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(URL, params={"api_key": TMDB_API_KEY, "query": movie_title})
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form)


@app.route('/select/<int:id>')
def select(id):
    url = f"https://api.themoviedb.org/3/movie/{id}?language=en-US"
    headers = {"accept": "application/json"}
    data = requests.get(url, headers=headers, params={"api_key": TMDB_API_KEY} ).json()
    # print(response.json())

    new_movie = Movie(
        title=data["title"],
        year=int(data["release_date"].split("-")[0]) if data.get("release_date") else 0,
        img_url = f"https://image.tmdb.org/t/p/w500{data['poster_path']}" if data.get("poster_path") else "",
        description=data["overview"],
    )

    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for('update', id=new_movie.id))

if __name__ == '__main__':
    app.run(debug=True)
