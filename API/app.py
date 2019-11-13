from flask import Flask
from flask import request
from SPARQLWrapper import SPARQLWrapper, JSON

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


# get the all the recipes if no filters are given
# else select the recipes that corresponds to the provided filter(s)
@app.route('/recette')
def getRecetteList():
    parameters = request.args

    # filter of the SPARQL query
    filter_clause = ""

    # filter on note
    # Add the filter only if the note is provided
    note = parameters.get('note')
    if note is not None:
        if filter_clause == "":
            filter_clause = "FILTER( xsd:float(?ratingValue)>" + note + " "
        else:
            filter_clause += "&& xsd:float(?ratingValue)>" + note + " "

    # filter on ingredient
    # Add the filter only if the ingredient is provided
    ingredients = parameters.get('ingredients')
    if ingredients is not None:
        if filter_clause == "":
            filter_clause = "FILTER( CONTAINS(str(?ingredients), '" + ingredients + "' ) "
        else:
            filter_clause += "&& CONTAINS(str(?ingredients), '" + ingredients + "' ) "

    # filter on tempDePrep
    # Add the filter only if the tempDePrep is provided
    tempDePrep = parameters.get('tempDePrep')
    if tempDePrep is not None:
        if filter_clause == "":
            filter_clause = 'FILTER( "'+tempDePrep+'"^^xsd:duration > xsd:duration(?totalTime) '
        else:
            filter_clause += '&& "'+tempDePrep+'"^^xsd:duration > xsd:duration(?totalTime) '

    # filter on typeCuisine
    # Add the filter only if the typeCuisine is provided
    typeCuisine = parameters.get('typeCuisine')
    if typeCuisine is not None:
        if filter_clause == "":
            filter_clause = "FILTER( CONTAINS(str(?cuisine),'" + typeCuisine + "' ) "
        else:
            filter_clause += "&& CONTAINS(str(?cuisine), '" + typeCuisine + "' ) "

    # NO SPARQL QUERY FOR NOW !!!!
    # filter on difficulty
    # Add the filter only if the difficulty is provided
    difficulty = parameters.get('difficulty')
    if difficulty is not None:
        if filter_clause == "":
            filter_clause = "FILTER( CONTAINS(str(?difficulty),'" + difficulty + "' ) "
        else:
            filter_clause += "&& CONTAINS(str(?difficulty), '" + difficulty + "' ) "

    # Close the parenthesis at the end of the clause
    if filter_clause != "":
        filter_clause += ")."

    query = """
        SELECT 
            ?recipe 
            ?desc 
            ?name 
            ?img
            ?cuisine
            (group_concat(?ingredients;separator = ',') as ?ingredients)
            ?totalTime
            ?ratingValue
            ?source
        WHERE
        {
            ?recipe a schema:Recipe;
            schema:description ?desc;
            schema:name ?name;
            schema:image ?img;
            schema:recipeCuisine ?cuisine;
            schema:ingredients ?ingredients;
            schema:ratingValue ?ratingValue;
            schema:totalTime ?totalTime;
            wdrs:describedby ?source.
            """ + filter_clause + """
        }
        GROUP BY ?recipe ?desc ?name ?img ?cuisine ?totalTime ?ratingValue ?source """

    sparql = SPARQLWrapper("http://linkeddata.uriburner.com/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return results


if __name__ == '__main__':
    app.run()
