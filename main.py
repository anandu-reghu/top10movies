from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField
from wtforms.validators import DataRequired
import requests

API_KEY = "a0fc4ff9126d365c57e8ed8e54f434a1"
API_ENDPOINT = "https://api.themoviedb.org/3/search/movie/"



app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)


class Movies(db.Model):
    """

    id, title, year, description, rating, ranking, review, img_url

    """

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(300), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, unique=True, nullable=True)
    review = db.Column(db.String(300), nullable=True)
    img_url = db.Column(db.String(300), unique=True, nullable=False)


# db.create_all()

# new_movie = Movies(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )

# db.session.add(new_movie)
# db.session.commit()


class RatingForm(FlaskForm):
    rating = DecimalField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")


class AddMovie(FlaskForm):
    title = StringField("Movie Title")
    submit = SubmitField("Add Movie")


@app.route("/")
def home():
    movies = Movies.query.order_by(Movies.rating.desc()).all()
    for i in range(len(movies)):
        movies[i].ranking = len(movies) - (10-i) + 1
    # db.session.commit()
    return render_template("index.html", movies=movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = RatingForm()
    id = request.args.get("id")
    movie = Movies.query.get(id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete")
def delete():
    id = request.args.get("id")
    movie = Movies.query.get(id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    movies = Movies.query.all()
    max_length = False
    if len(movies) == 10:
        max_length = True
    movie_form = AddMovie()
    if movie_form.validate_on_submit():
        movie_name = movie_form.title.data
        headers = {
            "api_key": API_KEY,
            "language": "en-US",
            "query": movie_name,
            "include_adult": "true"
        }
        response = requests.get(API_ENDPOINT, params=headers)
        response.raise_for_status()
        movie_data = response.json()["results"]
        
        return render_template("select.html", movies=movie_data)
    return render_template("add.html", movie_form=movie_form, max_length=max_length)


@app.route("/get-details")
def get_details():
    movie_id = request.args.get("id")
    headers = {
        "api_key": API_KEY,
        "language": "en-US",
    }
    if movie_id:
        response = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}", params=headers)
        response.raise_for_status()
        movie = response.json()
        new_movie = Movies(title=movie["title"],
                           year=movie["release_date"].split("-")[0],
                           description=movie["overview"],
                           img_url=f"https://image.tmdb.org/t/p/w500/{movie['poster_path']}"
                           )
        db.session.add(new_movie)
        db.session.commit()
        movie = Movies.query.filter_by(title=movie["title"]).first()
        return redirect(url_for('edit', id=movie.id))


if __name__ == '__main__':
    app.run(debug=True)
