try:
    import simplejson as json
except ImportError:
    import json

from django.http import HttpResponse

def response_success_json(input_dict={}):
    input_dict['result'] = 'sucess'
    response = json.dumps(input_dict)
    return HttpResponse(response, content_type='application/json')

def response_success_str(response):
    return HttpResponse(response, content_type='application/json')
    
def response_error_json(input_dict={}):
    ret_dict ={}
    ret_dict['result'] = 'failed'
    ret_dict.update(input_dict)   
    response = json.dumps(ret_dict)
    return HttpResponse(response, content_type='application/json')