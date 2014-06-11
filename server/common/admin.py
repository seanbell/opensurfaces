

# In the admin panel, when adding new fields,
# sets the 'user' field to be the current logged in user
# as the default
class AutoUserMixin(object):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs['initial'] = request.user.id
            return db_field.formfield(**kwargs)
        return super(AutoUserMixin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
