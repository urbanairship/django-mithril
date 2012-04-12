from django.shortcut import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from mithril.forms import WhitelistForm

class WhitelistEditor(object):
    template_list = 'mithril/whitelist_edit.html'
    form_class = WhitelistForm

    def __init__(self, obj_from_request):
        self.obj_from_request = obj_from_request

    def __call__(self, request, whitelist_pk=None, *args, **kwargs):
        against_object = self.obj_from_request(request, *args, **kwargs)
        whitelist = against_object.range_set.get(pk=whitelist_pk) if whitelist_pk else None
        form = self.form_class(whitelist, request.method == 'POST' and request.POST)

        if form.is_valid():
            form.save()
            return HttpResponseRedirect('.')

        return render_to_response(self.template_list, {
            'form':form,
            'whitelist':whitelist
        }, context_instance=RequestContext(request))
