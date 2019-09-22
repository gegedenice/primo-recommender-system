from flask import Flask, jsonify, abort, render_template,url_for,request
import urllib3
import pandas as pd
import pickle
import joblib
from py2neo import Graph
from json import dumps

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

df = pd.read_csv('SimilarityModel/data/export_SJA_nltk_complete.csv', sep = ';')
loaded_model = joblib.load('model2.pkl')
indices = pd.Series(df.index, index=df['num']).drop_duplicates()

@app.route('/recommand/<int:num>', methods = ['GET'])
def recommand(num):
    idx = indices[num]
    sim_scores = list(enumerate(loaded_model[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:11]
    item_indices = [i[0] for i in sim_scores]
    return df.iloc[item_indices,0:7].to_json(orient='records')

##Infos de connexions à l'instance Neo4j, remplacer les paramètres
graph = Graph("bolt://localhost:7687", auth=("neo4j", "neo4j"))

##API branchée sur Neo4j
@app.route('/recommand-graph/<num>', methods = ['GET'])   
def recommandByGraph(num):
    query = """MATCH (d1:Doc {num: '"""+num+"""'})<-[:HAS_LOAN]-(l:Lecteur)-[:HAS_LOAN]->(d2:Doc) RETURN d2.num AS num, COUNT(*) AS usersWhoAlsoWatched ORDER BY usersWhoAlsoWatched DESC LIMIT 10"""
    return dumps(graph.run(query).data()) 

##Alternative en cas de pb de connexion : API exploitant un export csv
@app.route('/recommand-graph-csv/<int:num>', methods = ['GET'])   
def recommandByGraphCsv(num):
    dfcsv = pd.read_csv('SimilarityModel/data/export_from_graph.csv', sep = ',')
    return dumps(dfcsv.loc[dfcsv.source == num].sort_values('usersWhoAlsoWatched', ascending=False)[:10].to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True)   