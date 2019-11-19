from flask import Flask, request, make_response
from SPARQLWrapper import SPARQLWrapper, JSON
import json
from string import digits

app = Flask(__name__)

known_ingredients = ['tomato', 'onion', 'carrot', 'lemon', 'celery', 'banana', 'mango', 'olive', 'saffron', 'coriander', 'parsley']


@app.route('/')
def hello_world():
    return 'Hello World!'


# get the all the recipes if no filters are given
# else select the recipes that corresponds to the provided filter(s)
@app.route('/listRecette')
def getRecetteList():
    parameters = request.args
    print(parameters)
    # filter of the SPARQL query
    filter_clause = ""

    # filter on multiple ingredients
    filter_ingredients = ""

    # filter on multiple ingredients
    filter_keywords = ""

    # filter on note
    # Add the filter only if the note is provided
    note = parameters.get('note')
    if note is not None and (note != ""):
        if filter_clause == "":
            filter_clause = "FILTER( xsd:float(?ratingValue)>" + note + " "
        else:
            filter_clause += "&& xsd:float(?ratingValue)>" + note + " "

    # filter on tempDePrep
    # Add the filter only if the tempDePrep is provided
    tempDePrep = parameters.get('tempDePrep')
    if tempDePrep is not None and (tempDePrep != ""):
        if filter_clause == "":
            filter_clause = 'FILTER( "' + tempDePrep + '"^^xsd:duration > xsd:duration(?totalTime) '
        else:
            filter_clause += '&& "' + tempDePrep + '"^^xsd:duration > xsd:duration(?totalTime) '

    # filter on typeCuisine
    # Add the filter only if the typeCuisine is provided
    typeCuisine = parameters.get('typeCuisine')
    if typeCuisine is not None and (typeCuisine != ''):
        typeCuisine = str.capitalize(typeCuisine)
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
    if ingredientsList is not None and (ingredientsList != ''):
        ingredients = ingredientsList.split(',')
        for ingredient in ingredients:
            if filter_ingredients == "":
                filter_ingredients = "FILTER( CONTAINS(str(?ingredients), '" + ingredient + "' ) "
            else:
                filter_ingredients += "&& CONTAINS(str(?ingredients), '" + ingredient.lower() + "' ) "

    # Close the parenthesis at the end of the clause
    if filter_ingredients != "":
        filter_ingredients += ")."

    # filter on keyword
    # Add the filter only if the keyword is provided
    keywordsList = parameters.get('keywords')
    print(keywordsList)
    if (keywordsList is not None) and (keywordsList != ''):
        keywords = keywordsList.split(' ')
        for keyword in keywords:
            keyword = keyword.lower()
            if filter_keywords == "":
                filter_keywords = "FILTER( CONTAINS(LCASE(str(?keywords)), '" + keyword + "' ) "
            else:
                filter_keywords += "|| CONTAINS(LCASE(str(?keywords)), '" + keyword.lower() + "' ) "

    # Close the parenthesis at the end of the clause
    if filter_keywords != "":
        filter_keywords += ")."

    query = """SELECT DISTINCT
            ?name 
            ?desc 
            ?img
            ?totalTime
            ?ratingValue
            ?source
        WHERE {
            {
            SELECT 
                ?desc 
                ?name 
                ?img
                ?totalTime
                ?ratingValue
                Min(?source) AS  ?source
                (group_concat(DISTINCT ?ingredients;separator = ";") as ?ingredients)
                (group_concat(DISTINCT ?keywords;separator = ";") as ?keywords)
            WHERE {
                SELECT DISTINCT
                    ?desc 
                    ?name 
                    ?img
                    ?ingredients
                    ?totalTime
                    ?ratingValue
                    ?source
                    ?keywords
                WHERE
                {
                    ?recipe a schema:Recipe;
                    schema:description ?desc;
                    schema:name ?name;
                    schema:image ?img;
                    schema:recipeCuisine ?cuisine;
                    schema:ingredients ?ingredients;
                    schema:keywords ?keywords;               
                    schema:ratingValue ?ratingValue;
                    schema:totalTime ?totalTime;
                    wdrs:describedby ?source.
                    """ + filter_clause + """
                }
            }
            GROUP BY ?desc ?name ?img ?totalTime ?ratingValue
            }
        """ + filter_ingredients + """  """ + filter_keywords + """
        } """

    print(query)
    # get the result of the query in json
    sparql = SPARQLWrapper("http://linkeddata.uriburner.com/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    # get summary for each recette
    results = mappingSmallSummary(results)
    resp = make_response(results)
    resp.headers.set('Access-Control-Allow-Origin', '*')
    print(results)
    return resp


# get the recipe's informations
# MUST HAVE ONLY ONE RESULT !!!!!
# use the recipe's name to get the provided informations
@app.route('/recette')
def getRecette():
    parameters = request.args
    name = parameters.get('name')
    # Ex : spanish-sardines-on-toast
    query = """ SELECT 
                    ?desc 
                    ?name 
                    ?img
                    ?cuisine
                    ?totalTime
                    ?ratingValue
                    ?calories
                    ?carbohydrate
                    ?fat
                    ?fiber
                    ?protein
                    ?saturatedFat
                    ?sodium
                    ?sugar
                    (group_concat(?ingredients;separator = ";") as ?ingredients)
                WHERE {
                    SELECT DISTINCT
                        ?desc 
                        ?name 
                        ?img
                        ?cuisine
                        ?ingredients
                        ?totalTime
                        ?ratingValue
                        ?calories
                        ?carbohydrate
                        ?fat
                        ?fiber
                        ?protein
                        ?saturatedFat
                        ?sodium
                        ?sugar
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
                        wdrs:describedby ?source;
                        schema:nutrition ?nutrition.
                        OPTIONAL { ?nutrition schema:calories ?calories. }
                        OPTIONAL { ?nutrition schema:carbohydrateContent ?carbohydrate. }
                        OPTIONAL { ?nutrition schema:fatContent ?fat. }
                        OPTIONAL { ?nutrition schema:fiberContent ?fiber. }
                        OPTIONAL { ?nutrition schema:proteinContent ?protein. }
                        OPTIONAL { ?nutrition schema:saturatedFatContent ?saturatedFat. }
                        OPTIONAL { ?nutrition schema:sodiumContent ?sodium. }
                        OPTIONAL { ?nutrition schema:sugarContent ?sugar. }
                        FILTER(CONTAINS(str(?source), "%s" )).
                    }
                }
                GROUP BY ?recipe ?desc ?name ?img ?cuisine ?totalTime ?ratingValue 
                    ?calories ?carbohydrate ?fat ?fiber ?protein ?saturatedFat ?sodium ?sugar """ % (name)
    # get the result of the query in json
    sparql = SPARQLWrapper("http://linkeddata.uriburner.com/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    # get infos recette
    results = mappingSummaryRecette(results)

    resp = make_response(results)
    # Permet de comuniquer sur des ports différents sur le navigateur
    # regle les problemes de CORS policy
    resp.headers.set('Access-Control-Allow-Origin', '*')
    return resp


def mappingSmallSummary(raw_data):
    list_recette = raw_data["results"]["bindings"]
    result = {}
    new_list = []
    for recette in list_recette:
        new_recette = {}
        # name & linkName
        name = recette["name"]["value"]
        name = name.replace('\n', ' ')
        new_recette["name"] = name
        linkName = recette["source"]["value"].split("/")
        new_recette["linkName"] = linkName[-1]
        # description
        desc = recette["desc"]["value"]
        desc = desc.replace("\n\n\n\n", "")
        desc = desc.replace("\n\n\n", "")
        desc = desc.replace("\n\n", "")
        desc = desc.replace("\n", " ")
        new_recette["description"] = desc
        # image
        new_recette["imgUrl"] = recette["img"]["value"]
        # total time
        time = changeTimeFormat(recette["totalTime"]["value"])
        new_recette["totalTime"] = time
        # ratingValue
        note = recette["ratingValue"]["value"]
        note = roundNote(note)
        new_recette["note"] = note
        new_list.append(new_recette)
    result["list_recette"] = new_list
    return result


def mappingSummaryRecette(raw_data):
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
    new_recette["imgUrl"] = recette["img"]["value"]
    # total time
    time = changeTimeFormat(recette["totalTime"]["value"])
    new_recette["totalTime"] = time
    # ratingValue
    note = recette["ratingValue"]["value"]
    note = roundNote(note)
    new_recette["note"] = note
    # cuisine
    new_recette["cuisine"] = recette["cuisine"]["value"]
    # nutrition
    new_recette["calories"] = recette["calories"]["value"]
    new_recette["carbohydrate"] = recette["carbohydrate"]["value"]
    new_recette["fat"] = recette["fat"]["value"]
    new_recette["fiber"] = recette["fiber"]["value"]
    new_recette["protein"] = recette["protein"]["value"]
    new_recette["saturatedFat"] = recette["saturatedFat"]["value"]
    new_recette["sodium"] = recette["sodium"]["value"]
    new_recette["sugar"] = recette["sugar"]["value"]
    # ingredients
    ingredientsList = recette["ingredients"]["value"]
    new_recette["ingredients"] = getListInfosIngredients(ingredientsList)
    return new_recette


# create a Json List with the ingredients ( and the url if the ingredient is in our glossaire)
# result : [ { "ingredient": ..., "url": ...},{...}, ... ]
def getListInfosIngredients(ingredientsList):
    list_ingredients = []
    ingredients = ingredientsList.split(';')
    for ingredient in ingredients:
        infosIngredientsJson = {}
        # if it is the hyperlink we take just what is just before ".jpg"
        if "http" in ingredient:
            # get the ingredient (after the last / and before .jpg
            new_ingredient = ingredient.rsplit('/', 1)[1]
            new_ingredient = new_ingredient.split('.jpg')[0]

            # clean the string :
            # remove the resized if it is in the string
            new_ingredient = new_ingredient.replace('-resized', '')
            # remove the %IGNORE if it is in the string
            new_ingredient = new_ingredient.replace('%', '')
            new_ingredient = new_ingredient.replace('IGNORE', '')
            # remove the "NEW"" if it is in the string
            new_ingredient = new_ingredient.replace('NEW', '')
            new_ingredient = new_ingredient.replace('-', ' ')
            new_ingredient = new_ingredient.replace('_', ' ')
            # remove number from the string
            remove_digits = str.maketrans('', '', digits)
            new_ingredient = new_ingredient.translate(remove_digits)
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


def changeTimeFormat(time):
    time = time.split('T')[1]
    if "M" in time:
        time += "in"
    time = time.lower()
    return time


def roundNote(note):
    note = float(note)
    note = round(note, 1)
    return note


@app.route('/infosingredients')
def getInfosingredients():
    parameters = request.args
    ingredient = parameters.get('ingredient')
    ingredient = str.capitalize(ingredient)

    query = """
         SELECT DISTINCT ?desc ?img
        WHERE {
            <http://dbpedia.org/resource/""" + ingredient + """> rdfs:comment ?desc;
            foaf:depiction ?img.
            FILTER langMatches(lang(?desc), 'en').
        }"""
    # get the result of the query in json
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    # get infos ingredient
    results = mappingSummaryIngredients(results)

    resp = make_response(results)
    # Permet de comuniquer sur des ports différents sur le navigateur
    # regle les problemes de CORS policy
    resp.headers.set('Access-Control-Allow-Origin', '*')
    return resp


def mappingSummaryIngredients(raw_data):
    infosIngredient_all = raw_data["results"]["bindings"][0]
    infosIngredient = {}
    # desc
    infosIngredient['desc'] = infosIngredient_all['desc']['value']
    # img
    infosIngredient['img'] = infosIngredient_all['img']['value']
    return infosIngredient


if __name__ == '__main__':
    app.run()
