

def update_requset_params(request, param_dict):
    rq = request.GET.copy();
    rq.update(param_dict)
    request.REQUEST.dicts = (request.POST, rq)
    return request