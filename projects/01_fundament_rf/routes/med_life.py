from flask import Blueprint, render_template, jsonify, abort
from services.med_life_loader import (
    list_objects, load_object, load_drug, load_prices,
    filter_by_system, collect_prescriptions, collect_labs,
    collect_subjective, build_system_scores, SYSTEM_LABELS
)

bp = Blueprint('med_life', __name__, url_prefix='/med-life')


@bp.route('/')
def index():
    return render_template('med_life/index.html', objects=list_objects())


@bp.route('/atlas/<object_id>')
def atlas(object_id):
    data = load_object(object_id)
    if not data:
        abort(404)
    scores = build_system_scores(object_id)
    return render_template('med_life/atlas.html',
                           object_id=object_id,
                           meta=data['meta'],
                           scores=scores,
                           labels=SYSTEM_LABELS)


@bp.route('/passport/<object_id>')
def passport(object_id):
    data = load_object(object_id)
    if not data:
        abort(404)
    drugs = collect_prescriptions(data['entries'])
    for d in drugs:
        d['ref'] = load_drug(d.get('drug_id'))
        d['prices'] = load_prices(d.get('drug_id'))
    labs = collect_labs(data['entries'])
    subjective = collect_subjective(data['entries'])
    return render_template('med_life/passport.html',
                           object_id=object_id,
                           data=data,
                           drugs=drugs,
                           labs=labs,
                           subjective=subjective)


@bp.route('/system/<object_id>/<system_key>')
def system_view(object_id, system_key):
    data = load_object(object_id)
    if not data:
        abort(404)
    if system_key not in SYSTEM_LABELS:
        abort(404)
    entries = filter_by_system(data['entries'], system_key)
    drugs = collect_prescriptions(entries)
    for d in drugs:
        d['ref'] = load_drug(d.get('drug_id'))
        d['prices'] = load_prices(d.get('drug_id'))
    labs = collect_labs(entries)
    return render_template('med_life/system_view.html',
                           object_id=object_id,
                           system_key=system_key,
                           system_label=SYSTEM_LABELS[system_key],
                           entries=entries,
                           drugs=drugs,
                           labs=labs)


@bp.route('/timeline/<object_id>')
def timeline(object_id):
    data = load_object(object_id)
    if not data:
        abort(404)
    entries = sorted(data['entries'], key=lambda x: x.get('date', '') or '')
    return render_template('med_life/timeline.html',
                           object_id=object_id,
                           meta=data['meta'],
                           entries=entries)


# ── JSON API ───────────────────────────────────────────────

@bp.route('/api/objects')
def api_objects():
    return jsonify(list_objects())


@bp.route('/api/<object_id>/entries')
def api_entries(object_id):
    data = load_object(object_id)
    if not data:
        abort(404)
    return jsonify(data)


@bp.route('/api/<object_id>/system/<system_key>')
def api_system(object_id, system_key):
    data = load_object(object_id)
    if not data:
        abort(404)
    return jsonify(filter_by_system(data['entries'], system_key))


@bp.route('/api/<object_id>/labs')
def api_labs(object_id):
    data = load_object(object_id)
    if not data:
        abort(404)
    return jsonify(collect_labs(data['entries']))


@bp.route('/api/<object_id>/drugs')
def api_drugs(object_id):
    data = load_object(object_id)
    if not data:
        abort(404)
    drugs = collect_prescriptions(data['entries'])
    for d in drugs:
        d['ref'] = load_drug(d.get('drug_id'))
        d['prices'] = load_prices(d.get('drug_id'))
    return jsonify(drugs)


@bp.route('/api/<object_id>/radar')
def api_radar(object_id):
    return jsonify(build_system_scores(object_id))


@bp.route('/api/<object_id>/timeline')
def api_timeline(object_id):
    data = load_object(object_id)
    if not data:
        abort(404)
    return jsonify(sorted(data['entries'], key=lambda x: x.get('date', '') or ''))
