# (c) 2012 Urban Airship and Contributors

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from mithril.forms import WhitelistForm
from mithril.middleware import WhitelistMiddleware
from mithril.utils import pre_django_1_9


class WhitelistEditor(object):

    template = 'mithril/whitelist_edit.html'
    form_class = WhitelistForm

    def __init__(self, obj_from_request):
        self.obj_from_request = obj_from_request

    def __call__(self, request, *args, **kwargs):
        whitelist = self.obj_from_request(request, *args, **kwargs)
        strategy = WhitelistMiddleware().get_strategy()
        current_ip = strategy.get_ip_from_request(request)

        form_args = (current_ip, whitelist)
        form_kwargs = {}
        if hasattr(self, 'range_form_class'):
            form_kwargs = {'range_form_class': self.range_form_class}

        if request.method == 'POST':
            form_args += (request.POST,)
        form = self.form_class(*form_args, **form_kwargs)
        if form.is_valid():
            self.save_form(request, form, *args, **kwargs)
            return HttpResponseRedirect('.')

        return self.respond(request, form, whitelist, *args, **kwargs)

    def save_form(self, request, form, *args, **kwargs):
        return form.save()

    def respond(self, request, form, whitelist, *args, **kwargs):
        if pre_django_1_9():
            return render_to_response(self.template, {
                'form':form,
                'whitelist':whitelist
            }, context_instance=RequestContext(request))
        else:
            return render_to_response(self.template, {
                'form':form,
                'whitelist':whitelist
            })
