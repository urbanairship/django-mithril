import mithril
from mithril.strategy import get_strategy_from_settings


class MithrilBackendBase(object):
    def authenticate(self, **kwargs):
        user = super(MithrilBackendBase, self).authenticate(**kwargs)
        strategy = get_strategy_from_settings()

        if not strategy.partial_credential_lookup:
            return user

        for key, lookup in strategy.partial_credential_lookup:
            val = kwargs.get(key, None)
            if val is not None:
                whitelists = strategy.model.objects.filter(**{lookup: val})

                # XXX: this is a hack to get the current
                # request IP by storing it in a well-known
                # location during the ``process_request``
                # portion of the middleware cycle.
                ip = mithril.get_current_ip()

                if strategy.validate_whitelists(
                        map(lambda w: w.okay(ip), whitelists)):
                    return user
                else:
                    # that user shouldn't login!
                    strategy.login_signal.send(
                        sender=self,
                        partial_credentials=val,
                        ip=ip,
                        whitelists=whitelists,
                    )
