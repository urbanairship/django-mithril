from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from mithril.forms import WhitelistForm
from mithril.middleware import WhitelistMiddleware


class WhitelistEditor(object):

    template = 'mithril/whitelist_edit.html'
    form_class = WhitelistForm

    def __init__(self, obj_from_request):
        self.obj_from_request = obj_from_request

    def __call__(self, request, whitelist_pk=None, *args, **kwargs):
        whitelist = self.obj_from_request(request, *args, **kwargs)
        strategy = WhitelistMiddleware().get_strategy()
        current_ip = strategy.get_ip_from_request(request)

        if request.method == 'POST':
            form = self.form_class(current_ip, whitelist, request.POST)
        else:
            self.form_class(current_ip, whitelist)
        if form.is_valid():
            self.save_form(request, form, *args, **kwargs)
            return HttpResponseRedirect('.')

        return self.respond(request, form, whitelist, *args, **kwargs)

    def save_form(self, request, form, *args, **kwargs):
        return form.save()

    def respond(self, request, form, whitelist, *args, **kwargs):
        return render_to_response(self.template, {
            'form':form,
            'whitelist':whitelist
        }, context_instance=RequestContext(request))
