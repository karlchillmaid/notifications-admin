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


@main.route("/services/<service_id>/service-settings/text-messages", methods=['GET'])
@login_required
@user_has_permissions('manage_service')
def service_settings_text_messages(service_id):
    inbound_number = inbound_number_client.get_inbound_sms_number_for_service(service_id)
    disp_inbound_number = inbound_number['data'].get('number', '')
    sms_senders = service_api_client.get_sms_senders(service_id)
    sms_sender_count = len(sms_senders)
    default_sms_sender = next(
        (Field(x['sms_sender'], html='escape') for x in sms_senders if x['is_default']), "None"
    )

    return render_template(
        'views/service-settings/text-messages/index.html',
        can_receive_inbound=('inbound_sms' in current_service['permissions']),
        inbound_number=disp_inbound_number,
        default_sms_sender=default_sms_sender,
        sms_sender_count=sms_sender_count,
    )


@main.route("/services/<service_id>/service-settings/set-sms", methods=['GET'])
@login_required
@user_has_permissions('manage_service')
def service_set_sms(service_id):
    return render_template(
        'views/service-settings/set-sms.html',
    )


@main.route("/services/<service_id>/service-settings/sms-prefix", methods=['GET', 'POST'])
@login_required
@user_has_permissions('manage_service')
def service_set_sms_prefix(service_id):

    form = SMSPrefixForm(enabled=(
        'on' if current_service['prefix_sms'] else 'off'
    ))

    form.enabled.label.text = 'Start all text messages with ‘{}:’'.format(current_service['name'])

    if form.validate_on_submit():
        service_api_client.update_service(
            current_service['id'],
            prefix_sms=(form.enabled.data == 'on')
        )
        return redirect(url_for('.service_settings', service_id=service_id))

    return render_template(
        'views/service-settings/sms-prefix.html',
        form=form
    )


@main.route("/services/<service_id>/service-settings/set-international-sms", methods=['GET', 'POST'])
@login_required
@user_has_permissions('manage_service')
def service_set_international_sms(service_id):
    form = InternationalSMSForm(
        enabled='on' if 'international_sms' in current_service['permissions'] else 'off'
    )
    if form.validate_on_submit():
        force_service_permission(
            service_id,
            'international_sms',
            on=(form.enabled.data == 'on'),
        )
        return redirect(
            url_for(".service_settings", service_id=service_id)
        )
    return render_template(
        'views/service-settings/set-international-sms.html',
        form=form,
    )


@main.route("/services/<service_id>/service-settings/set-inbound-sms", methods=['GET'])
@login_required
@user_has_permissions('manage_service')
def service_set_inbound_sms(service_id):
    number = inbound_number_client.get_inbound_sms_number_for_service(service_id)['data'].get('number', '')
    return render_template(
        'views/service-settings/set-inbound-sms.html',
        inbound_number=number,
    )


@main.route("/services/<service_id>/service-settings/sms-sender", methods=['GET'])
@login_required
@user_has_permissions('manage_service', 'manage_api_keys')
def service_sms_senders(service_id):

    def attach_hint(sender):
        hints = []
        if sender['is_default']:
            hints += ["default"]
        if sender['inbound_number_id']:
            hints += ["receives replies"]
        if hints:
            sender['hint'] = "(" + " and ".join(hints) + ")"

    sms_senders = service_api_client.get_sms_senders(service_id)

    for sender in sms_senders:
        attach_hint(sender)

    return render_template(
        'views/service-settings/sms-senders.html',
        sms_senders=sms_senders
    )


@main.route("/services/<service_id>/service-settings/sms-sender/add", methods=['GET', 'POST'])
@login_required
@user_has_permissions('manage_service')
def service_add_sms_sender(service_id):
    form = ServiceSmsSenderForm()
    sms_sender_count = len(service_api_client.get_sms_senders(service_id))
    first_sms_sender = sms_sender_count == 0
    if form.validate_on_submit():
        service_api_client.add_sms_sender(
            current_service['id'],
            sms_sender=form.sms_sender.data.replace('\r', '') or None,
            is_default=first_sms_sender if first_sms_sender else form.is_default.data
        )
        return redirect(url_for('.service_sms_senders', service_id=service_id))
    return render_template(
        'views/service-settings/sms-sender/add.html',
        form=form,
        first_sms_sender=first_sms_sender)


@main.route(
    "/services/<service_id>/service-settings/sms-sender/<sms_sender_id>/edit",
    methods=['GET', 'POST'],
    endpoint="service_edit_sms_sender"
)
@main.route(
    "/services/<service_id>/service-settings/sms-sender/<sms_sender_id>/delete",
    methods=['GET'],
    endpoint="service_confirm_delete_sms_sender"
)
@login_required
@user_has_permissions('manage_service')
def service_edit_sms_sender(service_id, sms_sender_id):
    sms_sender = service_api_client.get_sms_sender(service_id, sms_sender_id)
    is_inbound_number = sms_sender['inbound_number_id']
    if is_inbound_number:
        form = ServiceEditInboundNumberForm(is_default=sms_sender['is_default'])
    else:
        form = ServiceSmsSenderForm(**sms_sender)

    if form.validate_on_submit():
        service_api_client.update_sms_sender(
            current_service['id'],
            sms_sender_id=sms_sender_id,
            sms_sender=sms_sender['sms_sender'] if is_inbound_number else form.sms_sender.data.replace('\r', ''),
            is_default=True if sms_sender['is_default'] else form.is_default.data
        )
        return redirect(url_for('.service_sms_senders', service_id=service_id))

    form.is_default.data = sms_sender['is_default']
    return render_template(
        'views/service-settings/sms-sender/edit.html',
        form=form,
        sms_sender=sms_sender,
        inbound_number=is_inbound_number,
        sms_sender_id=sms_sender_id,
        confirm_delete=(request.endpoint == "main.service_confirm_delete_sms_sender")
    )


@main.route(
    "/services/<service_id>/service-settings/sms-sender/<sms_sender_id>/delete",
    methods=['POST'],
)
@login_required
@user_has_permissions('manage_service')
def service_delete_sms_sender(service_id, sms_sender_id):
    service_api_client.delete_sms_sender(
        service_id=current_service['id'],
        sms_sender_id=sms_sender_id,
    )
    return redirect(url_for('.service_sms_senders', service_id=service_id))
