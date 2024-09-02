import json
import azure.functions as func

def server_error(error):
    response = {
                "status":"failed",
                "error":str(error)
               }
    return func.HttpResponse( 
                json.dumps(response),
                status_code=500
            )

def input_required():
    response = {
                "status":"failed",
                "error":"scac code required"
               }
    return func.HttpResponse( 
                json.dumps(response),
                status_code=400
            )
    