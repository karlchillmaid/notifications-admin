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
from flask_login import login_required
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


@main.route("/services/<service_id>/service-settings/emails", methods=['GET'])
@login_required
@user_has_permissions('manage_service')
def service_settings_emails(service_id):
    reply_to_email_addresses = service_api_client.get_reply_to_email_addresses(service_id)
    reply_to_email_address_count = len(reply_to_email_addresses)
    default_reply_to_email_address = next(
        (x['email_address'] for x in reply_to_email_addresses if x['is_default']), "Not set"
    )

    return render_template(
        'views/service-settings/emails/index.html',
        default_reply_to_email_address=default_reply_to_email_address,
        reply_to_email_address_count=reply_to_email_address_count,
    )


@main.route("/services/<service_id>/service-settings/set-email", methods=['GET'])
@login_required
@user_has_permissions('manage_service')
def service_set_email(service_id):
    return render_template(
        'views/service-settings/set-email.html',
    )


@main.route("/services/<service_id>/service-settings/set-reply-to-email", methods=['GET'])
@login_required
@user_has_permissions('manage_service')
def service_set_reply_to_email(service_id):
    return redirect(url_for('.service_email_reply_to', service_id=service_id))


@main.route("/services/<service_id>/service-settings/email-reply-to", methods=['GET'])
@login_required
@user_has_permissions('manage_service', 'manage_api_keys')
def service_email_reply_to(service_id):
    reply_to_email_addresses = service_api_client.get_reply_to_email_addresses(service_id)
    return render_template(
        'views/service-settings/email_reply_to.html',
        reply_to_email_addresses=reply_to_email_addresses)


@main.route("/services/<service_id>/service-settings/email-reply-to/add", methods=['GET', 'POST'])
@login_required
@user_has_permissions('manage_service')
def service_add_email_reply_to(service_id):
    form = ServiceReplyToEmailForm()
    reply_to_email_address_count = len(service_api_client.get_reply_to_email_addresses(service_id))
    first_email_address = reply_to_email_address_count == 0
    if form.validate_on_submit():
        service_api_client.add_reply_to_email_address(
            current_service['id'],
            email_address=form.email_address.data,
            is_default=first_email_address if first_email_address else form.is_default.data
        )
        return redirect(url_for('.service_email_reply_to', service_id=service_id))
    return render_template(
        'views/service-settings/email-reply-to/add.html',
        form=form,
        first_email_address=first_email_address)


@main.route(
    "/services/<service_id>/service-settings/email-reply-to/<reply_to_email_id>/edit",
    methods=['GET', 'POST'],
    endpoint="service_edit_email_reply_to"
)
@main.route(
    "/services/<service_id>/service-settings/email-reply-to/<reply_to_email_id>/delete",
    methods=['GET'],
    endpoint="service_confirm_delete_email_reply_to"
)
@login_required
@user_has_permissions('manage_service')
def service_edit_email_reply_to(service_id, reply_to_email_id):
    form = ServiceReplyToEmailForm()
    reply_to_email_address = service_api_client.get_reply_to_email_address(service_id, reply_to_email_id)
    if request.method == 'GET':
        form.email_address.data = reply_to_email_address['email_address']
        form.is_default.data = reply_to_email_address['is_default']
    if form.validate_on_submit():
        service_api_client.update_reply_to_email_address(
            current_service['id'],
            reply_to_email_id=reply_to_email_id,
            email_address=form.email_address.data,
            is_default=True if reply_to_email_address['is_default'] else form.is_default.data
        )
        return redirect(url_for('.service_email_reply_to', service_id=service_id))
    return render_template(
        'views/service-settings/email-reply-to/edit.html',
        form=form,
        reply_to_email_address_id=reply_to_email_id,
        confirm_delete=(request.endpoint == "main.service_confirm_delete_email_reply_to"),
    )


@main.route("/services/<service_id>/service-settings/email-reply-to/<reply_to_email_id>/delete", methods=['POST'])
@login_required
@user_has_permissions('manage_service')
def service_delete_email_reply_to(service_id, reply_to_email_id):
    service_api_client.delete_reply_to_email_address(
        service_id=current_service['id'],
        reply_to_email_id=reply_to_email_id,
    )
    return redirect(url_for('.service_email_reply_to', service_id=service_id))
