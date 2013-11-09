# -*- coding: utf-8 -*-

'''
    Handle the Flask interface
'''

import os
import random
import sqlite3
from user import User
from job import Job
from fuzzywuzzy import process
from kNN import get_knn_result
from flask import render_template
from app import app


PATH_TO_DB = './db'
with open('user/data.txt', 'r') as f:
    data = []
    for line in f.readlines():
        element = line.rstrip()
        try:
            data.append(float(element))
        except:
            data.append(element)
    user = User(data)


CONNECTION = sqlite3.connect(os.path.join(PATH_TO_DB, 'formations.db'))

# Get all labels
all_labels = CONNECTION.execute(
    'SELECT global_categorie_name\
     FROM formations'
).fetchall()

all_labels = set(all_labels)
CONNECTION.close()


@app.route('/')
def index():
    '''
        Display the home page of the tool, allowing to search for a job
    '''

    # DB connection
    connection = sqlite3.connect(os.path.join(PATH_TO_DB, 'clustering_data.db'))
    query = ''' SELECT label_en FROM job_infos'''
    result = connection.execute(query)
    query_result = result.fetchall()
    connection.close()
    return render_template('index.html',
                           title='Orientation Scolaire',
                           jobs=query_result)


@app.route('/job/<job>')
def display_job(job):
    '''
        Retrieve all the useful data to display a job
    '''
    print 'job', job

    # Connect to the clustering database to get all the basic data
    connection = sqlite3.connect(os.path.join(PATH_TO_DB, 'clustering_data.db'))
    query = 'SELECT * FROM job_infos WHERE label_en="%s"' % (job)
    result = connection.execute(query)
    query_result = result.fetchone()
    print 'query_result', query_result
    # Keep track of data for header
    job_code = query_result[0]

    current_job = Job(job_code)

    # Get the similar jobs in the cluster
    connection = sqlite3.connect(os.path.join(PATH_TO_DB, 'clustering_data.db'))
    similar_jobs_result = connection.execute(
        'SELECT similar_job_code \
        FROM job_similar\
        WHERE job_code ="%s"' % (job_code))

    similar_job_codes = similar_jobs_result.fetchall()

    similar_jobs = []
    for code in similar_job_codes:
        similar_jobs.append(Job(code))
    connection.close()
    random.shuffle(similar_jobs)

    image_exists = os.path.isfile('./app/static/img/%s.jpg' % (current_job.job_code))

    # Get all the values in French
    connection = sqlite3.connect(os.path.join(PATH_TO_DB, 'formations.db'))
    job_fr_en = connection.execute(
        'SELECT *\
        FROM formations_fr_en\
        WHERE label_en=?', [job]
    ).fetchone()
    connection.close()
    if job_fr_en is None:
        is_job_fr_en = False
        job_fr_en_code = ''
        job_fr_en_label_en = ''
        job_fr_en_job_name = ''
        job_fr_en_description = ''
        job_fr_en_image_link = ''
        job_fr_en_job_niveau = ''
        job_fr_en_job_salaire = ''
    else:
        is_job_fr_en = True
        job_fr_en_code = job_fr_en[0]
        job_fr_en_label_en = job_fr_en[1]
        job_fr_en_job_name = job_fr_en[2].title()
        job_fr_en_description = job_fr_en[3]
        if job_fr_en[4] == '':
            job_fr_en_image_link = '/static/img/%s.jpg' % (current_job.job_code) \
                if image_exists else '/static/img/not_available.jpg'

        else:
            job_fr_en_image_link = job_fr_en[4]
        if job_fr_en[5] == '':
            job_fr_en_job_niveau = 'N/A'
        else:
            job_fr_en_job_niveau = job_fr_en[5]
        if job_fr_en[6] == '':
            job_fr_en_job_salaire = 'N/A'
        else:
            job_fr_en_job_salaire = job_fr_en[6]

    # Get the formation
    if job_fr_en is None or job_fr_en[2] is None or job_fr_en == '' or job_fr_en[2] == '':
        formations = 'N/A'
    else:
        connection = sqlite3.connect(os.path.join(PATH_TO_DB, 'formations.db'))
        formations = connection.execute(
            'SELECT formation_name, global_categorie_name, formation_url\
            FROM graphe_formation\
            WHERE job_name=?', [job_fr_en[2]]
        ).fetchall()
        formations = set(formations)
        connection.close()

    return render_template('job.html',
                           title=job,
                           current_job=current_job,
                           information=query_result,
                           user=user,
                           experience=query_result[1],
                           similar_jobs=similar_jobs,
                           job_fr_en=job_fr_en,
                           job_fr_en_code=job_fr_en_code,
                           job_fr_en_label_en=job_fr_en_label_en,
                           job_fr_en_job_name=job_fr_en_job_name,
                           job_fr_en_description=job_fr_en_description,
                           job_fr_en_image_link=job_fr_en_image_link,
                           job_fr_en_job_niveau=job_fr_en_job_niveau,
                           job_fr_en_job_salaire=job_fr_en_job_salaire,
                           is_job_fr_en=is_job_fr_en,
                           formations=formations)


@app.route('/account')
def account():
    '''
        Display the user parameters
    '''
    closest_job_code = get_knn_result(user.profile)
    similar_jobs = []
    for code in closest_job_code:
        similar_jobs.append(Job(code))

    return render_template('account.html',
                           user=user,
                           current_job='',
                           title='My account',
                           similar_jobs=similar_jobs)


@app.route('/formation/<formation>')
def display_formation(formation):
    '''
        Retrieve all the useful data to display a formation
    '''
    print 'formation', formation

    connection = sqlite3.connect(os.path.join(PATH_TO_DB, 'formations.db'))

    # Let's identify the correct string (encoding issue)
    label_found = process.extractOne(
        formation,
        all_labels
    )

    etablissements = connection.execute(
        'SELECT *\
         FROM formations\
         WHERE global_categorie_name=?', [label_found[0][0]]
    ).fetchall()

    # etablissements = connection.execute(
    #     'SELECT *\
    #      FROM formations\
    #      WHERE global_categorie_name=?', [formation]
    # ).fetchall()

    connection.close()

    return render_template('formation.html',
                           title=formation,
                           formation=formation,
                           etablissements=etablissements)


@app.route('/test')
def test_visualization():
    '''
        Function to test new features
    '''

    connection = sqlite3.connect(os.path.join(PATH_TO_DB, 'formations.db'))
    formations = connection.execute('SELECT * FROM formations').fetchall()
    formations_name = connection.execute(
        'SELECT global_categorie_name\
        FROM formations'
    ).fetchall()

    # etablissement = connection.execute('SELECT * FROM etablissement').fetchall()
    # ville = connection.execute('SELECT * FROM ville').fetchall()

    # for i in range(len(etablissement)):
    #     categorie_formation = connection.execute(
    #         'SELECT categorie_formation\
    #         FROM formations'
    #     ).fetchall()

    #     sous_categorie_formation = connection.execute(
    #         'SELECT sous_categorie_formation\
    #         FROM formations'
    #     ).fetchall()

    #     specialite = connection.execute(
    #         'SELECT specialite\
    #         FROM formations'
    #     ).fetchall()

    #     mention = connection.execute(
    #         'SELECT *\
    #         FROM mention'
    #     ).fetchall()
    job_fr_en = connection.execute(
        'SELECT * FROM formations_fr_en').fetchall()
    connection.close()

    connection = sqlite3.connect(os.path.join(PATH_TO_DB, 'onisepdata.db'))
    basic_infos = connection.execute('SELECT * FROM basic_infos').fetchall()
    bac2 = connection.execute('SELECT * FROM bac2').fetchall()
    bac3 = connection.execute('SELECT * FROM bac3').fetchall()
    connection.close()

    connection = sqlite3.connect(os.path.join(PATH_TO_DB, 'formations.db'))
    test = connection.execute('SELECT * FROM graphe_formation').fetchall()
    connection.close()

    return render_template('test.html',
                           title='TEST',
                           formations=formations,
                           basic_infos=basic_infos,
                           bac2=bac2,
                           bac3=bac3,
                           test=test)
