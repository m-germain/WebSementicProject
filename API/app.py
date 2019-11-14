from flask import Flask
from flask import request
from SPARQLWrapper import SPARQLWrapper, JSON
import json

app = Flask(__name__)

known_ingredients = ['tomato', 'onion', 'carot']

@app.route('/')
def hello_world():
    return 'Hello World!'


# get the all the recipes if no filters are given
# else select the recipes that corresponds to the provided filter(s)
@app.route('/listRecette')
def getRecetteList():
    parameters = request.args

    # filter of the SPARQL query
    filter_clause = ""

    # filter on multiple ingredients
    filter_ingredients = ""

    # filter on note
    # Add the filter only if the note is provided
    note = parameters.get('note')
    if note is not None:
        if filter_clause == "":
            filter_clause = "FILTER( xsd:float(?ratingValue)>" + note + " "
        else:
            filter_clause += "&& xsd:float(?ratingValue)>" + note + " "

    # filter on tempDePrep
    # Add the filter only if the tempDePrep is provided
    tempDePrep = parameters.get('tempDePrep')
    if tempDePrep is not None:
        if filter_clause == "":
            filter_clause = 'FILTER( "' + tempDePrep + '"^^xsd:duration > xsd:duration(?totalTime) '
        else:
            filter_clause += '&& "' + tempDePrep + '"^^xsd:duration > xsd:duration(?totalTime) '

    # filter on typeCuisine
    # Add the filter only if the typeCuisine is provided
    typeCuisine = parameters.get('typeCuisine')
    if typeCuisine is not None:
        if filter_clause == "":
            filter_clause = "FILTER( CONTAINS(str(?cuisine),'" + typeCuisine + "' ) "
        else:
            filter_clause += "&& CONTAINS(str(?cuisine), '" + typeCuisine + "' ) "

    # Close the parenthesis at the end of the clause
    if filter_clause != "":
        filter_clause += ")."

    # filter on ingredient
    # Add the filter only if the ingredient is provided
    ingredientsList = parameters.get('ingredients')
    if ingredientsList is not None:
        ingredients = ingredientsList.split(',')
        for ingredient in ingredients:
            if filter_ingredients == "":
                filter_ingredients = "FILTER( CONTAINS(str(?ingredients), '" + ingredient + "' ) "
            else:
                filter_ingredients += "&& CONTAINS(str(?ingredients), '" + ingredient + "' ) "

    # Close the parenthesis at the end of the clause
    if filter_ingredients != "":
        filter_ingredients += ")."

    query = """
        SELECT 
            ?name 
            ?desc 
            ?img
            ?totalTime
            ?ratingValue
        WHERE {
            {
            SELECT 
                ?desc 
                ?name 
                ?img
                ?totalTime
                ?ratingValue
                (group_concat(?ingredients;separator = ",") as ?ingredients)
            WHERE {
                SELECT DISTINCT
                    ?desc 
                    ?name 
                    ?img
                    ?ingredients
                    ?totalTime
                    ?ratingValue
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
            }
            GROUP BY ?desc ?name ?img ?totalTime ?ratingValue
            }
        """ + filter_ingredients + """ 
        } """
    # get the result of the query in json
    sparql = SPARQLWrapper("http://linkeddata.uriburner.com/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    # get summary for each recette
    results = getSummary(results)

    return results


# get the recipe's informations
# MUST HAVE ONLY ONE RESULT !!!!!
# use the recipe's name to get the provided informations
@app.route('/recette')
def getRecette():
    parameters = request.args
    name = "Indian mince with" #parameters.get('name')
    query = """
            SELECT 
                ?desc 
                ?name 
                ?img
                ?cuisine
                ?totalTime
                ?ratingValue
                (group_concat(?ingredients;separator = ",") as ?ingredients)
            WHERE {
                SELECT DISTINCT
                    ?desc 
                    ?name 
                    ?img
                    ?cuisine
                    ?ingredients
                    ?totalTime
                    ?ratingValue
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
                    FILTER(CONTAINS(str(?name),'""" + name + """' )).
                }
            }
            GROUP BY ?recipe ?desc ?name ?img ?cuisine ?totalTime ?ratingValue """
    # get the result of the query in json
    sparql = SPARQLWrapper("http://linkeddata.uriburner.com/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    # get infos recette
    results = getSummaryRecette(results)

    return results


def getSummary(raw_data):
    list_recette = raw_data["results"]["bindings"]
    result = {}
    new_list = []
    for recette in list_recette:
        new_recette = {}
        # name & linkName
        name = recette["name"]["value"]
        name = name.replace('\n', ' ')
        new_recette["name"] = name
        linkName = name.replace(' ', '-')
        new_recette["linkName"] = linkName
        # description
        desc = recette["desc"]["value"]
        desc = desc.replace("\n\n\n\n", "")
        desc = desc.replace("\n\n\n", "")
        desc = desc.replace("\n\n", "")
        desc = desc.replace("\n", " ")
        new_recette["description"] = desc
        # image
        new_recette["img"] = recette["img"]["value"]
        # total time
        new_recette["totalTime"] = recette["totalTime"]["value"]
        # ratingValue
        new_recette["ratingValue"] = recette["ratingValue"]["value"]
        new_list.append(new_recette)
    result["recette"] = new_list
    return result


def getSummaryRecette(raw_data):
    recette = raw_data["results"]["bindings"][0]
    new_recette = {}
    # name
    name = recette["name"]["value"]
    name = name.replace('\n', ' ')
    new_recette["name"] = name
    # description
    desc = recette["desc"]["value"]
    desc = desc.replace("\n\n\n\n", "")
    desc = desc.replace("\n\n\n", "")
    desc = desc.replace("\n\n", "")
    desc = desc.replace("\n", " ")
    new_recette["description"] = desc
    # image
    new_recette["img"] = recette["img"]["value"]
    # total time
    new_recette["totalTime"] = recette["totalTime"]["value"]
    # ratingValue
    new_recette["ratingValue"] = recette["ratingValue"]["value"]
    # cuisine
    new_recette["cuisine"] = recette["cuisine"]["value"]
    # ingredients
    ingredientsList = recette["ingredients"]["value"]
    new_recette["ingredients"] = getListInfosIngredients(ingredientsList)
    return new_recette

# create a Json List with the ingredients ( and the url if the ingredient is in our glossaire)
# result : [ { "ingredient": ..., "url": ...},{...}, ... ]
def getListInfosIngredients(ingredientsList):
    list_ingredients = []
    ingredients = ingredientsList.split(',')
    for ingredient in ingredients:
        infosIngredientsJson = {}
        # if it is the hyperlink we take just what is just before ".jpg"
        if "http" in ingredient:
            new_ingredient = ingredient.rsplit('/', 1)[1]
            new_ingredient = new_ingredient.split('.jpg')[0]
            infosIngredientsJson["ingredient"] = new_ingredient
            # add the ingredient's url only if the ingredient is in the known ingredients'list
            for ing in known_ingredients:
                if ing in new_ingredient:
                    infosIngredientsJson["url"] = "/glossaire/" + ing
                    break
        else:
            infosIngredientsJson["ingredient"] = ingredient
            # add the ingredient's url only if the ingredient is in the known ingredients'list
            for ing in known_ingredients:
                if ing in ingredient:
                    infosIngredientsJson["url"] = "/glossaire/" + ing
                    break
        list_ingredients.append(infosIngredientsJson)
    return list_ingredients


if __name__ == '__main__':
    app.run()
