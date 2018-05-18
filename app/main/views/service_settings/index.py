# from flask import (
#     abort,
#     current_app,
#     flash,
#     redirect,
#     render_template,
#     request,
#     session,
#     url_for,
# )
from flask_login import current_user, login_required
# from notifications_python_client.errors import HTTPError
# from notifications_utils.field import Field
# from notifications_utils.formatters import formatted_list

# from app import (
#     billing_api_client,
#     current_service,
#     email_branding_client,
#     inbound_number_client,
#     organisations_client,
#     service_api_client,
#     user_api_client,
#     zendesk_client,
# )
from app.main import main
# from app.main.forms import (
#     ConfirmPasswordForm,
#     FreeSMSAllowance,
#     InternationalSMSForm,
#     LetterBranding,
#     LinkOrganisationsForm,
#     OrganisationTypeForm,
#     RenameServiceForm,
#     RequestToGoLiveForm,
#     ServiceEditInboundNumberForm,
#     ServiceInboundNumberForm,
#     ServiceLetterContactBlockForm,
#     ServiceReplyToEmailForm,
#     ServiceSetBranding,
#     ServiceSmsSenderForm,
#     ServiceSwitchLettersForm,
#     SMSPrefixForm,
# )
from app.utils import (
    # AgreementInfo,
    # email_safe,
    # get_cdn_domain,
    user_has_permissions,
    # user_is_platform_admin,
)


@main.route("/services/<service_id>/service-settings/", methods=['GET'])
@login_required
@user_has_permissions('manage_service')
def service_settings(service_id):

    return render_template(
        'views/service-settings/index.html',
    )


@main.route("/services/<service_id>/service-settings/name", methods=['GET', 'POST'])
@login_required
@user_has_permissions('manage_service')
def service_name_change(service_id):
    form = RenameServiceForm()

    if request.method == 'GET':
        form.name.data = current_service.get('name')

    if form.validate_on_submit():
        unique_name = service_api_client.is_service_name_unique(service_id, form.name.data, email_safe(form.name.data))
        if not unique_name:
            form.name.errors.append("This service name is already in use")
            return render_template('views/service-settings/name.html', form=form)
        session['service_name_change'] = form.name.data
        return redirect(url_for('.service_name_change_confirm', service_id=service_id))

    return render_template(
        'views/service-settings/name.html',
        form=form)


@main.route("/services/<service_id>/service-settings/name/confirm", methods=['GET', 'POST'])
@login_required
@user_has_permissions('manage_service')
def service_name_change_confirm(service_id):
    # Validate password for form
    def _check_password(pwd):
        return user_api_client.verify_password(current_user.id, pwd)

    form = ConfirmPasswordForm(_check_password)

    if form.validate_on_submit():
        try:
            service_api_client.update_service(
                current_service['id'],
                name=session['service_name_change'],
                email_from=email_safe(session['service_name_change'])
            )
        except HTTPError as e:
            error_msg = "Duplicate service name '{}'".format(session['service_name_change'])
            if e.status_code == 400 and error_msg in e.message['name']:
                # Redirect the user back to the change service name screen
                flash('This service name is already in use', 'error')
                return redirect(url_for('main.service_name_change', service_id=service_id))
            else:
                raise e
        else:
            session.pop('service_name_change')
            return redirect(url_for('.service_settings', service_id=service_id))
    return render_template(
        'views/service-settings/confirm.html',
        heading='Change your service name',
        form=form)


@main.route("/services/<service_id>/service-settings/set-auth-type", methods=['GET'])
@login_required
@user_has_permissions('manage_service')
def service_set_auth_type(service_id):
    return render_template(
        'views/service-settings/set-auth-type.html',
    )

