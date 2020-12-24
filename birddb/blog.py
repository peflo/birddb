from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from birddb.auth import login_required
from birddb.db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    this_week = datetime.now().strftime("%Y%W")
    db = get_db()
    
    birds = db.execute(
        'SELECT DISTINCT b.id, common_name, info_url, picture_url, s.log_time, strftime("%Y%W",s.log_time) as week'
        ' FROM bird b'
        ' LEFT JOIN'
        ' ('
        '   SELECT bird_id, log_time'
        '   FROM sighting s'
        '   GROUP BY s.bird_id'
        '   ORDER BY log_time DESC'
        ' ) as s ON bird_id=b.id'
        ' ORDER BY week DESC, common_name ASC'
    ).fetchall()
    return render_template('blog/index.html', birds=birds, this_week=this_week)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        common_name = request.form['common_name']
        info_url = request.form['info_url']
        picture_url = request.form['picture_url']
        error = None

        if not common_name:
            error = 'Common Name is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO bird (common_name, info_url, picture_url)'
                ' VALUES (?, ?, ?)',
                (common_name, info_url, picture_url)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_bird(id):
    bird = get_db().execute(
        'SELECT b.id, common_name, info_url, picture_url'
        ' FROM bird b'
        ' WHERE b.id = ?',
        (id,)
    ).fetchone()

    if bird is None:
        abort(404, "Bird id {0} doesn't exist.".format(id))


    return bird


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    bird = get_bird(id)

    if request.method == 'POST':
        common_name = request.form['common_name']
        info_url = request.form['info_url']
        picture_url = request.form['picture_url']
        error = None

        if not common_name:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE bird SET common_name = ?, info_url = ?, picture_url = ?'
                ' WHERE id = ?',
                (common_name, info_url, picture_url, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))
    sightings = get_db().execute(
        'SELECT s.id, log_time, notes, user_id, username'
        ' FROM sighting s JOIN user u ON s.user_id = u.id'
        ' WHERE s.bird_id = ?',
        (id,)
      ).fetchall()
    return render_template('blog/update.html', bird=bird, sightings=sightings)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_bird(id)
    db = get_db()
    db.execute('DELETE FROM bird WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/<int:id>/sighting', methods=('GET','POST'))
@login_required
def sighting(id):
    bird = get_bird(id)
    if request.method == 'POST':
        notes = request.form['notes']

        db = get_db()
        db.execute(
            'INSERT INTO sighting (bird_id, notes, user_id)'
            ' VALUES (?, ?, ?)',
            (id, notes, g.user['id'])
        )
        db.commit()
        return redirect(url_for('blog.index'))
    return render_template('blog/sighting.html', bird=bird)

